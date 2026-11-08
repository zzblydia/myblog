#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal WebSocket client for real capture tests.

The client completes the HTTP Upgrade (optionally over TLS), optionally sends
masked text/binary messages, and then waits for the server to close.  The
audio bytes it sends are written to --expected-out for comparison.
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

LOG = logging.getLogger("mock_ws_client")


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
        path = Path(log_file or f"mock_ws_client_{time.strftime('%Y%m%d_%H%M%S')}.log")
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


def build_client_sends(case: str) -> tuple[list[list[bytes]], bytes]:
    if case == "none":
        return [], b""

    chunks = [ws.audio_chunk(seed) for seed in (11, 12, 13)]
    expected = b"".join(chunks)
    compress = case.startswith("pmd")
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15) if compress else None

    if case.endswith("_text") or case == "text":
        def frame(chunk: bytes, seq: int) -> bytes:
            payload = json_audio(chunk, seq)
            if compress:
                assert compressor is not None
                payload = ws.pmd_compress(compressor, payload)
            return ws.frame_bytes(1, payload, mask=True, rsv1=compress)

        # A complete JSON message split over two frames, followed by another
        # message.  This exercises masking, fragmentation and reassembly of a
        # text payload that the extractor must compact back to one line.
        first = frame(chunks[0], 1)
        fragmented = json_audio(chunks[1], 2)
        if compress:
            assert compressor is not None
            fragmented = ws.pmd_compress(compressor, fragmented)
        split = len(fragmented) // 2
        last = frame(chunks[2], 3)
        sends = [
            [first],
            [ws.frame_bytes(1, fragmented[:split], fin=False, mask=True,
                            rsv1=compress)],
            [ws.frame_bytes(0, fragmented[split:], fin=True, mask=True)],
            [last],
        ]
        return sends, expected

    def binary_frame(payload: bytes) -> bytes:
        if compress:
            assert compressor is not None
            payload = ws.pmd_compress(compressor, payload)
        return ws.frame_bytes(2, payload, mask=True, rsv1=compress)

    parts = [b"C2S-FRAG-A", b"C2S-FRAG-B"]
    large = ws.audio_chunk(77, 300)
    expected = chunks[0] + b"".join(parts) + chunks[1] + chunks[2] + large
    sends = [
        [binary_frame(chunks[0])],
        [ws.frame_bytes(2, parts[0], fin=False, mask=True)],
        [ws.frame_bytes(0, parts[1], fin=True, mask=True)],
        [binary_frame(chunks[1]), binary_frame(chunks[2])],
        [binary_frame(large)],
    ]
    return sends, expected


def connect(host: str, port: int, timeout: float = 10.0) -> socket.socket:
    deadline = time.monotonic() + timeout
    last_error: Optional[OSError] = None
    while time.monotonic() < deadline:
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.settimeout(timeout)
            return sock
        except OSError as exc:
            last_error = exc
            time.sleep(0.05)
    raise ConnectionError(f"cannot connect to {host}:{port}: {last_error}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Mock WebSocket client for capture tests")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int)
    parser.add_argument("--port-file")
    parser.add_argument("--send", default="none",
                        choices=("none", "binary", "text", "pmd_binary", "pmd_text"))
    parser.add_argument("--expected-out")
    parser.add_argument("--keylog")
    parser.add_argument("--tls", action="store_true", help="connect with TLS")
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--no-log-file", action="store_true")
    parser.add_argument("--log-file")
    args = parser.parse_args(argv)
    setup_logging(args.log_file, args.log_level, args.no_log_file)

    if args.port is None and not args.port_file:
        parser.error("--port or --port-file is required")
    port = args.port
    if port is None:
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            try:
                port = int(Path(args.port_file).read_text(encoding="ascii").strip())
                break
            except (OSError, ValueError):
                time.sleep(0.05)
        if port is None:
            raise ConnectionError(f"cannot read port from {args.port_file}")

    sock = connect(args.host, port)
    try:
        if args.tls:
            context = ws.make_client_context(args.keylog)
            sock = context.wrap_socket(sock, server_hostname="localhost")
            LOG.info("TLS established: %s %s", sock.version(),
                     sock.selected_alpn_protocol())

        # Always offer permessage-deflate.  The server only accepts it for its
        # pmd_* cases, so non-PMD tests are unaffected; s2c PMD tests still get
        # a negotiated context even though this client sends no payload.
        info = ws.client_handshake(sock, pmd=True)
        LOG.info("websocket upgrade done (pmd=%s)", info.get("pmd"))
        if args.send.startswith("pmd") and not info.get("pmd"):
            raise ConnectionError("permessage-deflate was not negotiated")

        sends, expected = build_client_sends(args.send)
        for batch in sends:
            for frame in batch:
                sock.sendall(frame)
            time.sleep(0.01)
        if args.expected_out:
            ws.write_expected(args.expected_out, expected)
        LOG.info("sent %d batches, expected audio %d bytes", len(sends), len(expected))

        # Wait for the server's close frame.
        ws.drain_frames(sock, idle_timeout=3.0)
    except Exception as exc:  # noqa: BLE001 - test helper
        LOG.error("client error: %s", exc)
        return 1
    finally:
        try:
            sock.close()
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
