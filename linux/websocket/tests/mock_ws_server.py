#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal WebSocket server used to produce real packets for capture tests.

The server binds an ephemeral port, writes it to --port-file, accepts exactly
one connection, performs the HTTP Upgrade (optionally over TLS) and then sends
a deterministic set of text or binary messages.  The concatenated audio bytes
are written to --expected-out so the test can compare them with the extractor
output.
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import socket
import ssl
import sys
import time
import zlib
from pathlib import Path
from typing import Optional, Sequence

import ws_mock_common as ws

LOG = logging.getLogger("mock_ws_server")


def setup_logging(log_file: Optional[str], level: str, no_file: bool) -> None:
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)
    if not no_file:
        path = Path(log_file or f"mock_ws_server_{time.strftime('%Y%m%d_%H%M%S')}.log")
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(fmt)
        root.addHandler(handler)


def json_audio(chunk: bytes, seq: int, pretty: bool = False) -> bytes:
    document = {
        "type": "audio",
        "seq": seq,
        "data": {"audio": base64.b64encode(chunk).decode("ascii")},
    }
    if pretty:
        return json.dumps(document, indent=2).encode("utf-8")
    return json.dumps(document, separators=(",", ":")).encode("utf-8")


def build_server_sends(case: str) -> tuple[list[list[bytes]], bytes]:
    """Return batches of frames and the expected concatenated audio."""
    if case == "none":
        return [], b""

    chunks = [ws.audio_chunk(seed) for seed in (1, 2, 3, 4)]
    expected = b"".join(chunks)
    compress = case.startswith("pmd")
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15) if compress else None

    if case.endswith("_text") or case == "text":
        def frame(chunk: bytes, seq: int, pretty: bool = False) -> bytes:
            payload = json_audio(chunk, seq, pretty)
            if compress:
                assert compressor is not None
                return ws.frame_bytes(1, ws.pmd_compress(compressor, payload), rsv1=True)
            return ws.frame_bytes(1, payload)

        sends = [
            [frame(chunks[0], 1)],
            [frame(chunks[1], 2, pretty=True)],
            [ws.frame_bytes(1, b'{"type":"control","op":"ping"}')],
            [frame(chunks[2], 3), frame(chunks[3], 4)],
        ]
        return sends, expected

    def binary_frame(payload: bytes) -> bytes:
        if compress:
            assert compressor is not None
            return ws.frame_bytes(2, ws.pmd_compress(compressor, payload), rsv1=True)
        return ws.frame_bytes(2, payload)

    # A single message, a fragmented message, two messages coalesced into one
    # write, and a message with a 16 bit extended length.
    parts = [b"FRAG-A", b"FRAG-B", b"FRAG-C"]
    large = ws.audio_chunk(99, 300)
    expected = chunks[0] + b"".join(parts) + chunks[1] + chunks[2] + large
    sends = [
        [binary_frame(chunks[0])],
        [ws.frame_bytes(2, parts[0], fin=False)],
        [ws.frame_bytes(0, parts[1], fin=False)],
        [ws.frame_bytes(0, parts[2], fin=True)],
        [binary_frame(chunks[1]), binary_frame(chunks[2])],
        [binary_frame(large)],
    ]
    return sends, expected


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Mock WebSocket server for capture tests")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--port-file", required=True)
    parser.add_argument("--case", default="binary",
                        choices=("binary", "text", "pmd_binary", "pmd_text", "none"))
    parser.add_argument("--expected-out")
    parser.add_argument("--cert")
    parser.add_argument("--key")
    parser.add_argument("--keylog")
    parser.add_argument("--hold", type=float, default=0.5,
                        help="seconds to keep the connection open after sending")
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--no-log-file", action="store_true")
    parser.add_argument("--log-file")
    args = parser.parse_args(argv)
    setup_logging(args.log_file, args.log_level, args.no_log_file)

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((args.host, args.port))
    listener.listen(1)
    actual_port = listener.getsockname()[1]
    Path(args.port_file).write_text(str(actual_port) + "\n", encoding="ascii")
    LOG.info("listening on %s:%d case=%s tls=%s",
             args.host, actual_port, args.case, bool(args.cert))

    connection: Optional[socket.socket] = None
    try:
        connection, peer = listener.accept()
        LOG.info("connection from %s:%d", peer[0], peer[1])
        connection.settimeout(15)

        if args.cert:
            context = ws.make_server_context(args.cert, args.key or args.cert, args.keylog)
            connection = context.wrap_socket(connection, server_side=True)
            LOG.info("TLS established: %s %s", connection.version(),
                     connection.selected_alpn_protocol())

        info = ws.server_handshake(connection, allow_pmd=args.case.startswith("pmd"))
        LOG.info("websocket upgrade done (pmd=%s)", info.get("pmd"))
        if args.case.startswith("pmd") and not info.get("pmd"):
            raise RuntimeError("permessage-deflate was not negotiated")

        sends, expected = build_server_sends(args.case)
        for batch in sends:
            for frame in batch:
                connection.sendall(frame)
            time.sleep(0.01)
        if args.expected_out:
            ws.write_expected(args.expected_out, expected)
        LOG.info("sent %d batches, expected audio %d bytes", len(sends), len(expected))

        # Drain anything the client sends (c2s tests) before closing.
        connection.settimeout(args.hold)
        ws.drain_frames(connection, idle_timeout=args.hold)
    except Exception as exc:  # noqa: BLE001 - test helper, report and exit
        LOG.error("server error: %s", exc)
        return 1
    finally:
        try:
            listener.close()
        except OSError:
            pass
        if connection is not None:
            try:
                ws.send_frame(connection, 0x8, b"")
            except OSError:
                pass
            try:
                connection.close()
            except OSError:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
