#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract complete WebSocket messages from a pcap with tshark.

tshark handles TLS decryption, TCP reassembly and the initial HTTP/WebSocket
classification.  The main path reads the fully reassembled byte stream from
`tshark -z follow,tls,raw` (or `follow,tcp,raw` for cleartext) and parses the
WebSocket frames locally.  This avoids a Wireshark dissector limitation: when
the HTTP 101 response and the first frames share one TCP segment or TLS record,
the dissector gives the whole range to the HTTP layer and never revisits it as
WebSocket.  A PDML-based path remains as a fallback for unusual captures.

The result is a compact, predictable .payload file.

Binary sessions:
    capture.payload is a raw byte stream: message1 + message2 + ...

Text sessions:
    capture.payload is UTF-8 JSON Lines: one complete JSON document per line.
    Whitespace outside JSON strings is removed so the document is guaranteed
    to stay on a single line.

TLS:
    Pass --keylog.  Wireshark's keylog parser understands the standard format
    and ignores the "#" comment lines that libwebsockets inserts.
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional, Sequence

LOG = logging.getLogger("ws_payload_dump")


class ExtractionError(RuntimeError):
    """Raised for a user-visible extraction failure."""


# ---------------------------------------------------------------------------
# logging
# ---------------------------------------------------------------------------

def setup_logging(prog: str, log_file: Optional[str], level: str, no_file: bool) -> Optional[Path]:
    """Configure file + console logging exactly once."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    numeric = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(numeric)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)

    if no_file:
        return None

    if log_file is None:
        log_file = f"{prog}_{time.strftime('%Y%m%d_%H%M%S')}.log"
    path = Path(log_file)
    if path.parent and str(path.parent) not in ("", "."):
        path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)
    return path


# ---------------------------------------------------------------------------
# data model
# ---------------------------------------------------------------------------

@dataclass
class WsMessage:
    frame: int
    timestamp: float
    stream: int
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    opcode: int
    fin: bool
    pmc: bool
    text: Optional[str] = None
    data: Optional[bytes] = None
    decompress_failed: bool = False
    not_fully_unmasked: bool = False

    @property
    def is_control(self) -> bool:
        return self.opcode in (0x8, 0x9, 0xA)

    @property
    def kind(self) -> Optional[str]:
        if self.text is not None:
            return "text"
        if self.data is not None:
            return "binary"
        return None


@dataclass
class DumpStats:
    stream: int
    server_port: Optional[int]
    client_port: Optional[int]
    direction: str
    payload_type: str
    messages: int = 0
    bytes_written: int = 0
    skipped: int = 0
    out_path: str = ""


# ---------------------------------------------------------------------------
# tshark helpers
# ---------------------------------------------------------------------------

def _tshark_base(tshark: str, pcap: str, keylog: Optional[str],
                 decode: Sequence[str]) -> list[str]:
    cmd = [tshark, "-r", pcap]
    if keylog:
        # Wireshark 3.x+ uses tls.keylog_file; older versions used ssl.*.
        cmd += ["-o", f"tls.keylog_file:{keylog}"]
    for value in decode:
        cmd += ["-d", value]
    return cmd


def _run_fields(base: list[str], display_filter: str, fields: Sequence[str]) -> str:
    cmd = base + ["-Y", display_filter, "-T", "fields", "-E", "occurrence=a"]
    for field in fields:
        cmd += ["-e", field]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or "").strip().splitlines()
        raise ExtractionError(
            "tshark failed: " + (" | ".join(detail[-5:]) if detail else "unknown error")
        )
    return result.stdout


def _tshark_version(tshark: str) -> str:
    try:
        result = subprocess.run([tshark, "-v"], capture_output=True, text=True)
        return (result.stdout or result.stderr).splitlines()[0]
    except (OSError, IndexError):
        return "unknown"


def discover(base: list[str], stream_filter: Optional[int]) -> tuple[list[int], dict[int, tuple[int, int]]]:
    """Return WS streams and a stream -> (client_port, server_port) map.

    A single tshark pass inspects WebSocket frames, HTTP 101 responses and TCP
    SYNs.  The 101 response is important because Wireshark can miss every
    WebSocket frame when the upgrade response and the first frames share one
    TCP segment/TLS record; the HTTP layer is still dissected.  The SYN gives
    us the client/server port orientation even when the upgrade was not
    captured.
    """
    display = ("websocket || http.response.code == 101 || "
               "(tcp.flags.syn == 1 && tcp.flags.ack == 0)")
    if stream_filter is not None:
        display = f"({display}) && tcp.stream == {stream_filter}"
    out = _run_fields(
        base, display,
        ["tcp.stream", "tcp.srcport", "tcp.dstport", "tcp.flags.syn",
         "tcp.flags.ack", "websocket.opcode", "http.response.code"],
    )

    streams: set[int] = set()
    ports: dict[int, tuple[int, int]] = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        stream_s, sport_s, dport_s, syn_s, ack_s, opcode_s, code_s = parts[:7]
        if not stream_s.isdigit():
            continue
        stream = int(stream_s)
        # A 101 response proves this is a WebSocket upgrade even if the frame
        # dissector produced nothing.
        if opcode_s.strip() or code_s.strip() == "101":
            streams.add(stream)
        if syn_s == "True" and ack_s != "True" and sport_s.isdigit() and dport_s.isdigit():
            # SYN without ACK is sent by the client: src=client, dst=server.
            ports[stream] = (int(sport_s), int(dport_s))
    return sorted(streams), ports


def direction_counts(base: list[str], stream: int) -> dict[int, int]:
    """Count complete data messages per source port.

    ``websocket.fin`` as a display filter only checks that the field exists,
    so the filter must compare it with 1; otherwise the opening frame of a
    fragmented message is counted as a complete message.  A packet may contain
    several messages, in which case tshark returns comma-separated occurrence
    lists that must be counted element by element.
    """
    out = _run_fields(
        base,
        f"tcp.stream == {stream} && websocket.fin == 1 && "
        "(websocket.opcode == 0 || websocket.opcode == 1 || websocket.opcode == 2)",
        ["tcp.srcport", "websocket.opcode", "websocket.fin"],
    )
    counts: dict[int, int] = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 3 or not parts[0].isdigit():
            continue
        port = int(parts[0])
        opcodes = parts[1].split(",") if parts[1] else []
        fins = parts[2].split(",") if parts[2] else []
        for index, opcode in enumerate(opcodes):
            fin = fins[index] if index < len(fins) else ""
            if fin == "True" and opcode in ("0", "1", "2"):
                counts[port] = counts.get(port, 0) + 1
    return counts


def count_frames(base: list[str], display_filter: str) -> int:
    return len([line for line in _run_fields(base, display_filter, ["frame.number"]).splitlines()
                if line.strip()])


def _drain(pipe, sink: list[str]) -> None:
    """Drain tshark stderr so a large capture cannot deadlock the pipe."""
    try:
        for raw in pipe:
            sink.append(raw.decode("utf-8", "replace"))
    except (ValueError, OSError):
        pass


def iter_messages(base: list[str], stream: int) -> Iterator[WsMessage]:
    """Yield every WebSocket layer tshark produced, in capture order."""
    cmd = base + ["-Y", f"websocket && tcp.stream == {stream}", "-T", "pdml"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None and proc.stderr is not None

    stderr_lines: list[str] = []
    drain = threading.Thread(target=_drain, args=(proc.stderr, stderr_lines), daemon=True)
    drain.start()

    try:
        for _, elem in ET.iterparse(proc.stdout, events=("end",)):
            if elem.tag != "packet":
                continue
            for message in parse_packet(elem):
                yield message
            elem.clear()
    finally:
        try:
            proc.stdout.close()
        except OSError:
            pass
        returncode = proc.wait()
        drain.join(timeout=5)
        if returncode != 0:
            tail = " | ".join(x.strip() for x in stderr_lines[-10:] if x.strip())
            raise ExtractionError(f"tshark pdml pass failed rc={returncode}: {tail}")


# ---------------------------------------------------------------------------
# reassembled stream parsing
# ---------------------------------------------------------------------------
#
# Wireshark has a blind spot: when the HTTP 101 response and the first
# WebSocket frames share one TCP segment (or one TLS record), the dissector
# hands the whole byte range to the HTTP layer and never revisits it as
# WebSocket.  `tshark -z follow,tls,raw` (and follow,tcp for cleartext)
# exposes the complete reassembled byte stream, so the frames can be parsed
# here instead of relying on the dissector's per-packet bookkeeping.

class StreamFallback(Exception):
    """Internal signal: the stream is not parseable as WebSocket; try PDML."""


def _drain_text(pipe, sink: list[str]) -> None:
    """Drain tshark stderr in a thread while stdout is consumed line by line."""
    try:
        for raw in pipe:
            sink.append(raw)
    except (ValueError, OSError):
        pass


@dataclass
class _FollowNode:
    index: int
    ip: str
    port: int


def _parse_node_line(line: str) -> Optional[_FollowNode]:
    """Parse 'Node 0: 192.0.2.1:443' or 'Node 1: [::1]:443'."""
    if not line.startswith("Node "):
        return None
    head, sep, endpoint = line.partition(":")
    if not sep:
        return None
    try:
        index = int(head.split()[1])
    except (IndexError, ValueError):
        return None
    host, sep, port = endpoint.strip().rpartition(":")
    if not sep or not port.isdigit():
        return None
    # Strip the brackets Wireshark adds around IPv6 addresses.
    return _FollowNode(index=index, ip=host.strip().strip("[]"), port=int(port))


@dataclass
class _Frame:
    fin: bool
    rsv1: bool
    opcode: int
    payload: bytes


def _peek_frame(buffer: bytearray, start: int) -> Optional[tuple[int, _Frame]]:
    """Parse one frame at *start* without consuming it.

    Returns ``(next_offset, frame)`` or ``None`` when the buffer does not yet
    contain a complete frame.  Keeping the cursor separate from the buffer lets
    the caller discard only the bytes that were actually parsed.
    """
    if len(buffer) - start < 2:
        return None
    b0 = buffer[start]
    b1 = buffer[start + 1]
    pos = start + 2

    length = b1 & 0x7F
    if length == 126:
        if len(buffer) - pos < 2:
            return None
        length = int.from_bytes(buffer[pos:pos + 2], "big")
        pos += 2
    elif length == 127:
        if len(buffer) - pos < 8:
            return None
        length = int.from_bytes(buffer[pos:pos + 8], "big")
        pos += 8

    mask_key: Optional[bytes] = None
    if b1 & 0x80:
        if len(buffer) - pos < 4:
            return None
        mask_key = bytes(buffer[pos:pos + 4])
        pos += 4

    if len(buffer) - pos < length:
        return None
    payload = bytes(buffer[pos:pos + length])
    if mask_key is not None:
        payload = bytes(byte ^ mask_key[i % 4] for i, byte in enumerate(payload))

    return pos + length, _Frame(
        fin=bool(b0 & 0x80),
        rsv1=bool(b0 & 0x40),
        opcode=b0 & 0x0F,
        payload=payload,
    )


class _StreamSession:
    """State shared by the two directions of one TCP stream."""

    def __init__(self, stream: int):
        self.stream = stream
        self.messages: list[WsMessage] = []
        self.client_port: Optional[int] = None
        self.server_port: Optional[int] = None
        self._sequence = 0

    def add_message(self, assembler: "_FrameAssembler", opcode: int,
                    rsv1: bool, data: Optional[bytes],
                    text: Optional[str]) -> None:
        self._sequence += 1
        self.messages.append(WsMessage(
            frame=self._sequence,
            timestamp=0.0,
            stream=self.stream,
            src_ip=assembler.src_ip,
            src_port=assembler.src_port,
            dst_ip=assembler.dst_ip,
            dst_port=assembler.dst_port,
            opcode=opcode,
            fin=True,
            pmc=rsv1,
            text=text,
            data=data,
        ))


class _FrameAssembler:
    """Incremental WebSocket frame/message parser for one direction."""

    def __init__(self, session: _StreamSession, node: _FollowNode,
                 peer: _FollowNode, on_decompress_error: str):
        self.session = session
        self.src_ip = node.ip
        self.src_port = node.port
        self.dst_ip = peer.ip
        self.dst_port = peer.port
        self.on_decompress_error = on_decompress_error
        self.buffer = bytearray()
        # A single inflater is kept across messages because permessage-deflate
        # uses context takeover by default (RFC 7692 section 7.2.3.2).
        self.inflater: Optional[zlib.Decompress] = None
        self.frag_opcode: Optional[int] = None
        self.frag_rsv1 = False
        self.frag_data = bytearray()

    def feed(self, data: bytes) -> None:
        self.buffer.extend(data)
        offset = 0
        while True:
            parsed = _peek_frame(self.buffer, offset)
            if parsed is None:
                break
            offset, frame = parsed
            self._on_frame(frame)
        if offset:
            del self.buffer[:offset]

    def _inflate(self, payload: bytes) -> bytes:
        # RFC 7692 strips the trailing 00 00 ff ff of Z_SYNC_FLUSH.  Put it
        # back so the shared decompressor can finish the block and retain its
        # sliding window for the next compressed message.
        if self.inflater is None:
            self.inflater = zlib.decompressobj(-15)
        try:
            return self.inflater.decompress(payload + b"\x00\x00\xff\xff")
        except zlib.error as exc:
            raise ExtractionError(
                f"permessage-deflate decompression failed: {exc}") from exc

    def _on_frame(self, frame: _Frame) -> None:
        if frame.opcode in (0x8, 0x9, 0xA):
            # Control frames may be interleaved with a fragmented message.
            return

        if frame.opcode in (0x1, 0x2):
            if self.frag_opcode is not None:
                raise ExtractionError(
                    "protocol error: new data frame while a fragmented message is open")
            if frame.fin:
                self._emit(frame.opcode, frame.rsv1, frame.payload)
            else:
                # RSV1 is only set on the first fragment; the compressed
                # payload is the concatenation of every fragment.
                self.frag_opcode = frame.opcode
                self.frag_rsv1 = frame.rsv1
                self.frag_data = bytearray(frame.payload)
            return

        if frame.opcode == 0x0:
            if self.frag_opcode is None:
                raise ExtractionError(
                    "protocol error: continuation frame without an open message")
            self.frag_data.extend(frame.payload)
            if frame.fin:
                opcode = self.frag_opcode
                rsv1 = self.frag_rsv1
                payload = bytes(self.frag_data)
                self.frag_opcode = None
                self.frag_data.clear()
                self._emit(opcode, rsv1, payload)
            return

        raise ExtractionError(f"unsupported WebSocket opcode 0x{frame.opcode:x}")

    def _emit(self, opcode: int, rsv1: bool, payload: bytes) -> None:
        if rsv1:
            try:
                payload = self._inflate(payload)
            except ExtractionError as exc:
                if self.on_decompress_error == "skip":
                    LOG.warning("%s (message skipped)", exc)
                    return
                raise
        if opcode == 0x2:
            self.session.add_message(self, opcode, rsv1, payload, None)
            return
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ExtractionError(
                f"text message is not valid UTF-8: {exc}") from exc
        self.session.add_message(self, opcode, rsv1, None, text)


class _DirectionState:
    """Buffers the HTTP upgrade, then hands the remainder to a frame parser."""

    def __init__(self, node: _FollowNode, peer: _FollowNode,
                 on_decompress_error: str):
        self.node = node
        self.peer = peer
        self.on_decompress_error = on_decompress_error
        self.http_buffer = bytearray()
        self.handshake_done = False
        self.assembler: Optional[_FrameAssembler] = None

    def feed(self, session: _StreamSession, data: bytes) -> None:
        if not self.handshake_done:
            self.http_buffer.extend(data)
            data = b""

            # "GET " starts a request and "HTTP/" starts a response.  A valid
            # WebSocket frame cannot start with either byte sequence, so any
            # other first byte means the capture started after the upgrade.
            first = self.http_buffer[0] if self.http_buffer else None
            if first is not None and first not in (ord("G"), ord("H")):
                data = bytes(self.http_buffer)
                self.http_buffer.clear()
                self.handshake_done = True
            else:
                marker = self.http_buffer.find(b"\r\n\r\n")
                if marker < 0:
                    if len(self.http_buffer) > 65536:
                        raise StreamFallback(
                            "no HTTP upgrade header at the start of the stream")
                    return
                header = bytes(self.http_buffer[:marker])
                data = bytes(self.http_buffer[marker + 4:])
                self.http_buffer.clear()
                self._parse_handshake(session, header)
                self.handshake_done = True

        if data:
            if self.assembler is None:
                self.assembler = _FrameAssembler(
                    session, self.node, self.peer, self.on_decompress_error)
            self.assembler.feed(data)

    def _parse_handshake(self, session: _StreamSession, header: bytes) -> None:
        lines = header.decode("latin-1").split("\r\n")
        first = lines[0] if lines else ""

        if first.startswith("GET "):
            # The endpoint that sends the request is the client.
            if session.client_port is None:
                session.client_port = self.node.port
            return

        if first.startswith("HTTP/"):
            if " 101 " not in f" {first} ":
                raise StreamFallback(f"unexpected HTTP response: {first}")
            if session.server_port is None:
                session.server_port = self.node.port
            return

        raise StreamFallback(f"unexpected HTTP first line: {first!r}")


def _iter_follow_output(base: list[str], stream: int,
                        use_tls: bool) -> Iterator[tuple[str, object]]:
    """Yield ('node', _FollowNode) and ('data', (index, bytes)) in order."""
    proto = "tls" if use_tls else "tcp"
    cmd = base + ["-q", "-z", f"follow,{proto},raw,{stream}"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    assert proc.stdout is not None and proc.stderr is not None

    stderr_lines: list[str] = []
    drain = threading.Thread(target=_drain_text,
                             args=(proc.stderr, stderr_lines), daemon=True)
    drain.start()

    try:
        for raw_line in proc.stdout:
            line = raw_line.rstrip("\n")
            node = _parse_node_line(line)
            if node is not None:
                yield "node", node
                continue
            if (not line or line.startswith("=") or line.startswith("Follow:")
                    or line.startswith("Filter:")):
                continue

            # A leading tab marks Node 1; lack of it marks Node 0.
            index = 1 if line.startswith("\t") else 0
            hexdata = line.strip()
            if not hexdata:
                continue
            try:
                chunk = bytes.fromhex(hexdata)
            except ValueError:
                LOG.debug("follow output: ignoring non-hex line %r", line[:80])
                continue
            yield "data", (index, chunk)
    finally:
        try:
            proc.stdout.close()
        except OSError:
            pass
        returncode = proc.wait()
        drain.join(timeout=5)
        if returncode != 0:
            tail = " | ".join(x.strip() for x in stderr_lines[-5:] if x.strip())
            raise ExtractionError(
                f"tshark follow pass failed rc={returncode}: {tail}")


def collect_stream_messages(
    base: list[str], stream: int, *, use_tls: bool,
    on_decompress_error: str = "error",
) -> tuple[list[WsMessage], dict[int, int], Optional[int], Optional[int]]:
    """Parse the whole TCP/TLS stream and return messages in arrival order.

    The return value also carries the number of data messages per source port
    and the client/server ports inferred from the HTTP upgrade.  A
    ``StreamFallback`` is raised when the bytes do not look like WebSocket at
    all, so the caller can retry with the PDML path.
    """
    session = _StreamSession(stream)

    # Node lines always precede data lines.  The first data line can only be
    # processed after both endpoints are known (for the peer address), so keep
    # a small queue for the unlikely case of data arriving first.
    nodes: dict[int, _FollowNode] = {}
    states: dict[int, _DirectionState] = {}
    pending: list[tuple[int, bytes]] = []

    def start_states() -> None:
        if len(nodes) < 2 or states:
            return
        left, right = list(nodes.values())
        states[left.index] = _DirectionState(left, right, on_decompress_error)
        states[right.index] = _DirectionState(right, left, on_decompress_error)
        for index, chunk in pending:
            if index in states:
                states[index].feed(session, chunk)
        pending.clear()

    for kind, payload in _iter_follow_output(base, stream, use_tls):
        if kind == "node":
            node = payload
            nodes[node.index] = node  # type: ignore[assignment]
            start_states()
            continue
        index, chunk = payload  # type: ignore[misc]
        if states:
            state = states.get(index)
            if state is not None:
                state.feed(session, chunk)
        else:
            pending.append((index, chunk))

    if len(nodes) < 2:
        raise StreamFallback("follow output did not contain two TCP endpoints")

    counts: dict[int, int] = {}
    for message in session.messages:
        counts[message.src_port] = counts.get(message.src_port, 0) + 1

    for state in states.values():
        if state.http_buffer:
            LOG.warning("direction %s: %d bytes of an incomplete HTTP upgrade",
                        state.node.port, len(state.http_buffer))
        if state.assembler is not None and state.assembler.buffer:
            LOG.warning("direction %s: %d trailing bytes (truncated frame?)",
                        state.node.port, len(state.assembler.buffer))

    if not session.messages:
        raise StreamFallback("no complete WebSocket data messages in the stream")

    return session.messages, counts, session.client_port, session.server_port


def _stream_is_tls(base: list[str], stream: int) -> bool:
    """True when the stream carries a TLS handshake (decrypted or not)."""
    return count_frames(base, f"tcp.stream == {stream} && tls.handshake") > 0


# ---------------------------------------------------------------------------
# PDML parsing
# ---------------------------------------------------------------------------

def _field_text(packet: ET.Element, name: str) -> Optional[str]:
    node = packet.find(f".//field[@name='{name}']")
    return node.get("show") if node is not None else None


def _field_int(packet: ET.Element, name: str) -> Optional[int]:
    value = _field_text(packet, name)
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def _field_float(packet: ET.Element, name: str) -> Optional[float]:
    value = _field_text(packet, name)
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def parse_packet(packet: ET.Element) -> list[WsMessage]:
    """Turn one PDML <packet> into zero or more complete WebSocket messages.

    tshark emits one <proto name="websocket"> per WebSocket frame, in document
    order.  Binary payloads are handed to the "data" dissector, which appears
    directly after the WebSocket layer as a data.data field.  Text payloads live
    in websocket.payload.text inside the WebSocket layer.
    """
    frame = _field_int(packet, "frame.number")
    timestamp = _field_float(packet, "frame.time_epoch")
    stream = _field_int(packet, "tcp.stream")
    src_port = _field_int(packet, "tcp.srcport")
    dst_port = _field_int(packet, "tcp.dstport")
    if None in (frame, timestamp, stream, src_port, dst_port):
        return []

    src_ip = _field_text(packet, "ip.src") or ""
    dst_ip = _field_text(packet, "ip.dst") or ""

    messages: list[WsMessage] = []
    current: Optional[WsMessage] = None

    for elem in packet.iter():
        if elem.tag == "proto" and elem.get("name") == "websocket":
            opcode = 0
            fin = False
            pmc = False
            for field in elem.findall("field"):
                name = field.get("name")
                if name == "websocket.opcode":
                    try:
                        opcode = int(field.get("show") or "0")
                    except ValueError:
                        opcode = 0
                elif name == "websocket.fin":
                    fin = field.get("show") == "True"
                elif name == "websocket.pmc":
                    pmc = field.get("show") == "True"
            text_node = elem.find(".//field[@name='websocket.payload.text']")
            current = WsMessage(
                frame=frame,
                timestamp=timestamp,
                stream=stream,
                src_ip=src_ip,
                src_port=src_port,
                dst_ip=dst_ip,
                dst_port=dst_port,
                opcode=opcode,
                fin=fin,
                pmc=pmc,
                text=text_node.get("show") if text_node is not None else None,
            )
            messages.append(current)

        elif elem.tag == "field" and elem.get("name") == "data.data" and current is not None:
            # A binary message's payload is the data.data field that follows
            # its WebSocket layer.  Text layers have text set, never data.
            if current.text is None and current.data is None and current.fin:
                raw = (elem.get("value") or elem.get("show") or "").replace(":", "")
                try:
                    current.data = bytes.fromhex(raw)
                except ValueError:
                    LOG.warning("frame %s: invalid data.data hex", current.frame)
            current = None

    # A non-fragmented text frame with invalid UTF-8 can fall through to the
    # data dissector.  Continuation frames (opcode 0) must not be guessed this
    # way: a fragmented binary message also ends with opcode 0.
    for message in messages:
        if message.opcode == 1 and message.text is None and message.data is not None:
            try:
                message.text = message.data.decode("utf-8")
                message.data = None
            except UnicodeDecodeError:
                pass

    if packet.find(".//field[@name='websocket.decompression.failed.expert']") is not None and messages:
        messages[-1].decompress_failed = True
    if packet.find(".//field[@name='websocket.payload.not.fully.unmasked']") is not None and messages:
        messages[-1].not_fully_unmasked = True
    return messages


# ---------------------------------------------------------------------------
# text normalisation
# ---------------------------------------------------------------------------

def compact_json_text(text: str) -> str:
    """Return a semantic-preserving one-line version of a JSON document.

    This is a lexical pass, not a re-serialisation: key order, duplicate keys,
    number formatting and base64 values are preserved byte for byte.  Raw
    control characters inside strings (invalid JSON) are escaped so the result
    still fits on one line.
    """
    text = text.lstrip("\ufeff")
    out: list[str] = []
    in_string = False
    escaped = False

    for ch in text:
        if in_string:
            if escaped:
                out.append(ch)
                escaped = False
            elif ch == "\\":
                out.append(ch)
                escaped = True
            elif ch == '"':
                out.append(ch)
                in_string = False
            elif ch == "\n":
                out.append("\\n")
            elif ch == "\r":
                out.append("\\r")
            elif ch == "\t":
                out.append("\\t")
            elif ord(ch) < 0x20:
                out.append("\\u%04x" % ord(ch))
            else:
                out.append(ch)
        else:
            if ch in " \t\r\n":
                continue
            out.append(ch)
            if ch == '"':
                in_string = True
    return "".join(out)


def _raw_b64_json(text: str) -> str:
    payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return json.dumps({"__raw_b64__": payload}, separators=(",", ":"))


# ---------------------------------------------------------------------------
# extraction
# ---------------------------------------------------------------------------

def _choose_direction(args_direction: str, counts: dict[int, int],
                      server_port: Optional[int], client_port: Optional[int]
                      ) -> tuple[Optional[int], str]:
    """Resolve --direction into a source-port filter (None means both)."""
    if args_direction == "both":
        return None, "both"

    if args_direction == "auto":
        if len(counts) == 1:
            port = next(iter(counts))
            if server_port is not None and port == server_port:
                return port, "s2c"
            if client_port is not None and port == client_port:
                return port, "c2s"
            return port, f"srcport={port}"
        if not counts:
            raise ExtractionError("no complete WebSocket data messages found")
        raise ExtractionError(
            "both directions carry complete WebSocket data messages "
            f"({counts}); please pass --direction s2c or --direction c2s"
        )

    if args_direction == "s2c":
        if server_port is None:
            if len(counts) == 1:
                server_port = next(iter(counts))
            else:
                raise ExtractionError("cannot determine the server port; pass --server-port")
        return server_port, "s2c"

    if args_direction == "c2s":
        if client_port is None:
            candidates = [p for p in counts if p != server_port]
            if len(candidates) == 1:
                client_port = candidates[0]
            else:
                raise ExtractionError("cannot determine the client port; pass --server-port")
        return client_port, "c2s"

    raise ExtractionError(f"unsupported direction: {args_direction}")


def _tls_diagnostics(base: list[str], *, keylog_present: bool) -> None:
    """Explain the most common reasons a capture yields no WebSocket frames."""
    tls_handshakes = count_frames(base, "tls.handshake")
    upgrades = count_frames(base, "http.response.code == 101")
    LOG.error("no complete WebSocket frames were found")
    LOG.error("diagnostics: tls.handshake frames=%d, http 101 responses=%d",
              tls_handshakes, upgrades)
    if tls_handshakes and upgrades == 0:
        if not keylog_present:
            LOG.error("TLS traffic was captured; pass --keylog FILE so tshark can "
                      "decrypt it")
            LOG.error("the keylog must belong to this session and the capture must "
                      "include the TLS handshake")
        else:
            LOG.error("the capture looks like TLS but the HTTP upgrade was not decrypted")
            LOG.error("check: the keylog belongs to this session and the capture contains "
                      "the handshake; libwebsockets writes $SSLKEYLOGFILE.<vhost> "
                      "(not the bare path)")
            LOG.error("non-standard TLS port: try --decode tcp.port==PORT,tls")
    elif upgrades == 0:
        LOG.error("no HTTP 101 response: the capture may start mid-session")
    elif upgrades:
        LOG.error("HTTP upgrade exists, but WebSocket dissection did not happen; "
                  "try --decode tcp.port==PORT,ws")


def extract_to_file(
    pcap: str,
    out_path: Path,
    *,
    tshark: str = "tshark",
    keylog: Optional[str] = None,
    decode: Sequence[str] = (),
    stream: Optional[int] = None,
    server_port: Optional[int] = None,
    direction: str = "auto",
    payload_type: str = "auto",
    invalid_text: str = "error",
    on_decompress_error: str = "error",
) -> DumpStats:
    """Extract a single WebSocket session into out_path and return statistics."""
    base = _tshark_base(tshark, pcap, keylog, decode)

    streams, syn_ports = discover(base, stream)
    if stream is None:
        if not streams:
            _tls_diagnostics(base, keylog_present=bool(keylog))
            raise ExtractionError("no WebSocket stream found in the capture")
        if len(streams) > 1:
            raise ExtractionError(
                f"capture contains multiple WebSocket streams {streams}; pass --stream N")
        stream = streams[0]
    elif stream not in streams:
        LOG.warning("tcp.stream %s has no WebSocket frames according to tshark", stream)

    syn_client, syn_server = syn_ports.get(stream, (None, None))
    client_port = syn_client
    if server_port is None:
        server_port = syn_server

    use_tls = _stream_is_tls(base, stream)
    if use_tls and not keylog:
        raise ExtractionError(
            "the WebSocket session is protected by TLS; pass --keylog FILE")

    # Prefer the reassembled-stream parser.  It sees every byte, including the
    # first frames that Wireshark's dissector loses when they share a segment
    # with the HTTP 101 response.  PDML remains as a fallback for captures the
    # stream parser cannot classify.
    stream_messages: Optional[list[WsMessage]] = None
    try:
        stream_messages, counts, hs_client, hs_server = collect_stream_messages(
            base, stream, use_tls=use_tls,
            on_decompress_error=on_decompress_error)
        if client_port is None:
            client_port = hs_client
        if server_port is None:
            server_port = hs_server
    except StreamFallback as exc:
        LOG.warning("stream parser could not handle this capture (%s); "
                    "falling back to tshark PDML", exc)
        counts = direction_counts(base, stream)

    LOG.info("WebSocket stream=%s client_port=%s server_port=%s",
             stream, client_port, server_port)
    LOG.info("complete data messages per source port: %s", counts)
    selected_src, direction_label = _choose_direction(direction, counts, server_port, client_port)

    if payload_type == "auto":
        # The first data message decides.  A later message of the other kind
        # aborts the run so that no data is silently dropped.
        LOG.info("payload type: auto (decided by the first complete data message)")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_name(out_path.name + f".tmp.{os.getpid()}")
    stats = DumpStats(
        stream=stream,
        server_port=server_port,
        client_port=client_port,
        direction=direction_label,
        payload_type=payload_type,
        out_path=str(out_path),
    )
    chosen_type: Optional[str] = None

    try:
        with open(tmp_path, "wb") as out:
            messages_iter: Iterable[WsMessage] = (
                stream_messages if stream_messages is not None
                else iter_messages(base, stream)
            )
            for message in messages_iter:
                if message.is_control:
                    continue
                if not message.fin:
                    # The PDML fallback reports opening fragments separately;
                    # the stream parser already reassembles them.
                    continue
                if message.not_fully_unmasked:
                    LOG.warning("frame %s: payload was not fully unmasked", message.frame)
                if message.decompress_failed:
                    text = f"frame {message.frame}: permessage-deflate decompression failed"
                    if on_decompress_error == "skip":
                        LOG.warning("%s (skipped)", text)
                        stats.skipped += 1
                        continue
                    raise ExtractionError(text)
                if selected_src is not None and message.src_port != selected_src:
                    continue

                kind = message.kind
                if kind is None:
                    LOG.warning("frame %s: complete message has no payload", message.frame)
                    stats.skipped += 1
                    continue

                if payload_type == "auto":
                    if chosen_type is None:
                        chosen_type = kind
                        LOG.info("payload type selected from first message: %s", kind)
                    elif kind != chosen_type:
                        raise ExtractionError(
                            f"mixed payload types in one session: first={chosen_type}, "
                            f"frame {message.frame}={kind}; pass --type binary or --type text"
                        )
                elif kind != payload_type:
                    LOG.debug("frame %s: skipping %s message while extracting %s",
                              message.frame, kind, payload_type)
                    stats.skipped += 1
                    continue

                if kind == "binary":
                    assert message.data is not None
                    if not message.data:
                        LOG.warning("frame %s: empty binary message skipped", message.frame)
                        stats.skipped += 1
                        continue
                    out.write(message.data)
                    stats.bytes_written += len(message.data)
                else:
                    assert message.text is not None
                    if message.text == "":
                        LOG.warning("frame %s: empty text message skipped", message.frame)
                        stats.skipped += 1
                        continue
                    compacted = compact_json_text(message.text)
                    try:
                        json.loads(compacted)
                    except (ValueError, json.JSONDecodeError) as exc:
                        if invalid_text == "skip":
                            LOG.warning("frame %s: invalid JSON skipped: %s", message.frame, exc)
                            stats.skipped += 1
                            continue
                        if invalid_text == "b64":
                            compacted = _raw_b64_json(message.text)
                            LOG.warning("frame %s: invalid JSON preserved as __raw_b64__",
                                        message.frame)
                        else:
                            raise ExtractionError(
                                f"frame {message.frame}: text message is not valid JSON: {exc}"
                            )
                    out.write(compacted.encode("utf-8"))
                    out.write(b"\n")
                    stats.bytes_written += len(compacted.encode("utf-8")) + 1

                stats.messages += 1

        if stats.messages == 0:
            raise ExtractionError(
                "no complete data messages matched the selected direction/type"
            )

        os.chmod(tmp_path, 0o600)
        tmp_path.replace(out_path)
    except BaseException:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise

    stats.payload_type = chosen_type or payload_type
    LOG.info("wrote %d messages, %d bytes to %s (skipped %d)",
             stats.messages, stats.bytes_written, out_path, stats.skipped)
    return stats


# ---------------------------------------------------------------------------
# probe
# ---------------------------------------------------------------------------

def probe(pcap: str, *, tshark: str, keylog: Optional[str], decode: Sequence[str]) -> None:
    base = _tshark_base(tshark, pcap, keylog, decode)
    LOG.info("tshark: %s", _tshark_version(tshark))
    LOG.info("keylog: %s", keylog or "<none>")
    streams, ports = discover(base, None)
    LOG.info("ws streams: %s", streams or "<none>")
    for stream in streams:
        client_port, server_port = ports.get(stream, (None, None))
        # Report the dissector count and the stream-parser count side by side:
        # a difference is the signature of the coalesced-upgrade bug.
        pdml_counts = direction_counts(base, stream)
        LOG.info("stream %s: client_port=%s server_port=%s pdml_messages=%s",
                 stream, client_port, server_port, pdml_counts)

        use_tls = _stream_is_tls(base, stream)
        if use_tls and not keylog:
            LOG.info("stream %s: TLS detected but no keylog was supplied", stream)
            continue
        try:
            _, counts, hs_client, hs_server = collect_stream_messages(
                base, stream, use_tls=use_tls)
        except (StreamFallback, ExtractionError) as exc:
            LOG.info("stream %s: stream parser failed: %s", stream, exc)
            continue
        LOG.info("stream %s: tls=%s stream_messages=%s client_port=%s server_port=%s",
                 stream, use_tls, counts,
                 client_port or hs_client, server_port or hs_server)
    LOG.info("tls.handshake frames: %d", count_frames(base, "tls.handshake"))
    LOG.info("http 101 responses: %d", count_frames(base, "http.response.code == 101"))


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------

def _load_builder():
    path = Path(__file__).resolve().parent / "tests" / "ws_pcap_builder.py"
    if not path.exists():
        raise ExtractionError(f"self-test builder not found: {path}")
    spec = importlib.util.spec_from_file_location("ws_pcap_builder", path)
    if spec is None or spec.loader is None:
        raise ExtractionError(f"cannot load self-test builder: {path}")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves annotations through sys.modules[cls.__module__].
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _recursive_values(obj, key: str):
    if isinstance(obj, dict):
        for name, value in obj.items():
            if name == key:
                yield value
            yield from _recursive_values(value, key)
    elif isinstance(obj, list):
        for item in obj:
            yield from _recursive_values(item, key)


def run_selftest() -> int:
    tshark = shutil.which("tshark")
    if not tshark:
        LOG.error("tshark is required for --selftest")
        return 2
    builder = _load_builder()
    failures = 0

    with tempfile.TemporaryDirectory(prefix="ws_selftest_") as tmpdir:
        tmp = Path(tmpdir)
        for name in ("binary", "text", "pmd_binary", "pmd_text"):
            case = builder.build_case(name)
            pcap = tmp / f"{name}.pcap"
            pcap.write_bytes(case.pcap)
            expected_type = "text" if "text" in name else "binary"
            out = tmp / f"{name}.payload"
            try:
                stats = extract_to_file(
                    str(pcap), out, tshark=tshark, direction="s2c",
                    payload_type=expected_type,
                )
            except ExtractionError as exc:
                LOG.error("selftest %s FAILED: %s", name, exc)
                failures += 1
                continue

            if expected_type == "binary":
                actual = out.read_bytes()
                if actual != case.expected_binary:
                    LOG.error("selftest %s FAILED: binary mismatch got=%d expected=%d",
                              name, len(actual), len(case.expected_binary))
                    failures += 1
                    continue
            else:
                chunks = []
                ok = True
                for line in out.read_text(encoding="utf-8").splitlines():
                    try:
                        doc = json.loads(line)
                    except json.JSONDecodeError as exc:
                        LOG.error("selftest %s FAILED: invalid JSON line: %s", name, exc)
                        ok = False
                        break
                    for value in _recursive_values(doc, "audio"):
                        if isinstance(value, str):
                            chunks.append(base64.b64decode(value))
                if not ok or b"".join(chunks) != case.expected_text_audio:
                    LOG.error("selftest %s FAILED: text audio mismatch got=%d expected=%d",
                              name, len(b"".join(chunks)), len(case.expected_text_audio))
                    failures += 1
                    continue

            LOG.info("selftest %s OK (%d messages, %d bytes)",
                     name, stats.messages, stats.bytes_written)

        # Direction filtering: the binary case also carries a client message.
        case = builder.build_case("binary")
        pcap = tmp / "c2s.pcap"
        pcap.write_bytes(case.pcap)
        out = tmp / "c2s.payload"
        try:
            extract_to_file(str(pcap), out, tshark=tshark, direction="c2s",
                            payload_type="binary")
            if out.read_bytes() != b"C2S-DATA":
                LOG.error("selftest direction FAILED: %r", out.read_bytes())
                failures += 1
            else:
                LOG.info("selftest direction c2s OK")
        except ExtractionError as exc:
            LOG.error("selftest direction c2s FAILED: %s", exc)
            failures += 1

    if failures:
        LOG.error("selftest finished with %d failure(s)", failures)
        return 1
    LOG.info("selftest finished OK")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract complete WebSocket messages from a pcap via tshark.",
    )
    parser.add_argument("--pcap", help="input pcap/pcapng file")
    parser.add_argument("--keylog", help="TLS keylog file (same session as the capture)")
    parser.add_argument("--out", help="output .payload file (default: <pcap>.payload)")
    parser.add_argument("--stream", type=int, help="tcp.stream number (auto if unique)")
    parser.add_argument("--server-port", type=int, help="server TCP port (for s2c/c2s)")
    parser.add_argument("--direction", choices=("auto", "s2c", "c2s", "both"),
                        default="auto", help="which direction carries the payload")
    parser.add_argument("--type", choices=("auto", "binary", "text"),
                        default="auto", help="payload type written to .payload")
    parser.add_argument("--invalid-text", choices=("error", "skip", "b64"),
                        default="error", help="behaviour for non-JSON text messages")
    parser.add_argument("--on-decompress-error", choices=("error", "skip"),
                        default="error", help="behaviour for deflate failures")
    parser.add_argument("--decode", action="append", default=[], metavar="RULE",
                        help="extra tshark -d rule, e.g. tcp.port==8443,tls")
    parser.add_argument("--tshark", default="tshark", help="tshark executable")
    parser.add_argument("--probe", action="store_true", help="log session diagnostics")
    parser.add_argument("--selftest", action="store_true", help="run built-in tests")
    parser.add_argument("--log-file", help="log path (default: <prog>_<timestamp>.log)")
    parser.add_argument("--log-level", default="INFO",
                        help="DEBUG/INFO/WARNING/ERROR (default INFO)")
    parser.add_argument("--no-log-file", action="store_true", help="console logging only")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging("ws_payload_dump", args.log_file, args.log_level, args.no_log_file)

    try:
        if args.selftest:
            return run_selftest()
        if not args.pcap:
            parser.error("--pcap is required unless --selftest is used")
        tshark = shutil.which(args.tshark) or (
            args.tshark if Path(args.tshark).is_file() else None)
        if not tshark:
            raise ExtractionError(f"tshark not found: {args.tshark}")
        if not Path(args.pcap).exists():
            raise ExtractionError(f"pcap not found: {args.pcap}")
        if args.keylog and not Path(args.keylog).exists():
            raise ExtractionError(f"keylog not found: {args.keylog}")

        if args.probe:
            probe(args.pcap, tshark=tshark, keylog=args.keylog, decode=args.decode)

        out = Path(args.out) if args.out else Path(args.pcap).with_suffix(".payload")
        stats = extract_to_file(
            args.pcap, out,
            tshark=tshark,
            keylog=args.keylog,
            decode=args.decode,
            stream=args.stream,
            server_port=args.server_port,
            direction=args.direction,
            payload_type=args.type,
            invalid_text=args.invalid_text,
            on_decompress_error=args.on_decompress_error,
        )
        LOG.info("summary: stream=%d direction=%s type=%s messages=%d bytes=%d out=%s",
                 stats.stream, stats.direction, stats.payload_type,
                 stats.messages, stats.bytes_written, stats.out_path)
        return 0
    except ExtractionError as exc:
        LOG.error("%s", exc)
        return 2
    except KeyboardInterrupt:
        LOG.warning("interrupted")
        return 130
    except OSError as exc:
        LOG.error("I/O error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
