#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build deterministic WebSocket pcaps for the extractor self-test.

Everything is generated in memory with the standard library only:

    Ethernet + IPv4 + TCP + HTTP Upgrade + WebSocket frames.

The purpose is to exercise the tshark based extractor without depending on a
live capture or on hand-installed tools beyond tshark itself.
"""

from __future__ import annotations

import base64
import hashlib
import json
import struct
import zlib
from dataclasses import dataclass, field
from typing import Optional

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

CLIENT_IP = "10.0.0.1"
SERVER_IP = "10.0.0.2"
CLIENT_PORT = 50000
SERVER_PORT = 8080

ETH_HEADER = bytes.fromhex("0200000000020200000000010800")


# ---------------------------------------------------------------------------
# generic helpers
# ---------------------------------------------------------------------------

def _checksum(data: bytes) -> int:
    """Internet checksum (RFC 1071)."""
    if len(data) % 2:
        data += b"\x00"
    total = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return (~total) & 0xFFFF


def _ipv4(src: str, dst: str, payload: bytes, ident: int) -> bytes:
    src_b = bytes(map(int, src.split(".")))
    dst_b = bytes(map(int, dst.split(".")))
    hdr = struct.pack(
        "!BBHHHBBH4s4s",
        0x45, 0, 20 + len(payload), ident, 0x4000, 64, 6, 0, src_b, dst_b,
    )
    hdr = hdr[:10] + struct.pack("!H", _checksum(hdr)) + hdr[12:]
    return hdr + payload


def _tcp(src_ip: str, dst_ip: str, sport: int, dport: int, seq: int,
         ack: int, flags: int, data: bytes = b"") -> bytes:
    hdr = struct.pack("!HHIIBBHHH", sport, dport, seq, ack, 0x50, flags, 65535, 0, 0)
    pseudo = struct.pack(
        "!4s4sBBH",
        bytes(map(int, src_ip.split("."))),
        bytes(map(int, dst_ip.split("."))),
        0, 6, len(hdr) + len(data),
    )
    hdr = hdr[:16] + struct.pack("!H", _checksum(pseudo + hdr + data)) + hdr[18:]
    return hdr + data


def ws_frame(
    opcode: int,
    payload: bytes,
    *,
    fin: bool = True,
    mask: bool = False,
    rsv1: bool = False,
    mask_key: bytes = b"\x11\x22\x33\x44",
) -> bytes:
    """Encode one WebSocket frame."""
    b0 = (0x80 if fin else 0) | (0x40 if rsv1 else 0) | opcode
    length = len(payload)
    mask_bit = 0x80 if mask else 0
    if length < 126:
        hdr = bytes([b0, mask_bit | length])
    elif length < 65536:
        hdr = bytes([b0, mask_bit | 126]) + struct.pack("!H", length)
    else:
        hdr = bytes([b0, mask_bit | 127]) + struct.pack("!Q", length)
    if mask:
        body = bytes(c ^ mask_key[i % 4] for i, c in enumerate(payload))
        return hdr + mask_key + body
    return hdr + payload


def ws_accept(key: str) -> str:
    """Compute Sec-WebSocket-Accept."""
    return base64.b64encode(hashlib.sha1((key + WS_GUID).encode()).digest()).decode()


def pmd_compress(compressor: zlib.Compress, data: bytes) -> bytes:
    """Compress one permessage-deflate message (context takeover preserved)."""
    # RFC 7692: strip the trailing 00 00 ff ff of Z_SYNC_FLUSH.
    return compressor.compress(data) + compressor.flush(zlib.Z_SYNC_FLUSH)[:-4]


# ---------------------------------------------------------------------------
# pcap writer
# ---------------------------------------------------------------------------

class TcpFlow:
    """A tiny TCP conversation writer with plausible sequence numbers."""

    def __init__(self, client_port: int = CLIENT_PORT, server_port: int = SERVER_PORT):
        self.client_port = client_port
        self.server_port = server_port
        self.client_seq = 1001
        self.server_seq = 2001
        self.packets: list[bytes] = []
        self.timestamp = 1700000000.0
        self.ident = 0

    def _packet(self, from_client: bool, flags: int, data: bytes = b"") -> None:
        self.ident += 1
        if from_client:
            src_ip, dst_ip = CLIENT_IP, SERVER_IP
            sport, dport = self.client_port, self.server_port
            seq, ack = self.client_seq, self.server_seq
        else:
            src_ip, dst_ip = SERVER_IP, CLIENT_IP
            sport, dport = self.server_port, self.client_port
            seq, ack = self.server_seq, self.client_seq
        payload = _tcp(src_ip, dst_ip, sport, dport, seq, ack, flags, data)
        self.packets.append(ETH_HEADER + _ipv4(src_ip, dst_ip, payload, self.ident))

    def syn(self) -> None:
        # Real three-way handshake so tshark can derive relative sequence
        # numbers.  A SYN consumes one sequence number, so the first data byte
        # must not reuse the initial sequence value (otherwise tshark drops it
        # as an overlap and the HTTP upgrade loses its first character).
        self._packet(True, 0x02)
        self.client_seq += 1
        self._packet(False, 0x12)
        self.server_seq += 1
        self._packet(True, 0x10)

    def data(self, from_client: bool, data: bytes) -> None:
        self._packet(from_client, 0x18, data)
        if from_client:
            self.client_seq += len(data)
        else:
            self.server_seq += len(data)

    def to_pcap(self) -> bytes:
        out = [struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)]
        for i, packet in enumerate(self.packets):
            ts = self.timestamp + i * 0.001
            sec = int(ts)
            usec = int(round((ts - sec) * 1_000_000))
            out.append(struct.pack("<IIII", sec, usec, len(packet), len(packet)))
            out.append(packet)
        return b"".join(out)


# ---------------------------------------------------------------------------
# scenario construction
# ---------------------------------------------------------------------------

@dataclass
class PcapCase:
    name: str
    pcap: bytes
    server_port: int
    client_port: int
    expected_binary: bytes = b""
    expected_text_audio: bytes = b""
    expected_text_messages: list[dict] = field(default_factory=list)


def _handshake(flow: TcpFlow, pmd: bool) -> None:
    key = "dGhlIHNhbXBsZSBub25jZQ=="
    request = (
        "GET /ws HTTP/1.1\r\n"
        "Host: example\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
    )
    if pmd:
        request += "Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits\r\n"
    request += "\r\n"

    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {ws_accept(key)}\r\n"
    )
    if pmd:
        response += "Sec-WebSocket-Extensions: permessage-deflate\r\n"
    response += "\r\n"

    flow.data(True, request.encode())
    flow.data(False, response.encode())


def _audio_chunk(seed: int, size: int = 96) -> bytes:
    # Deterministic pseudo-audio bytes, including 0x00 and 0x0a on purpose.
    return bytes(((seed * 37 + i * 11) & 0xFF) for i in range(size))


def _text_audio_message(chunk: bytes, seq: int, pretty: bool = False) -> bytes:
    obj = {
        "type": "audio",
        "seq": seq,
        "data": {"audio": base64.b64encode(chunk).decode()},
    }
    if pretty:
        return json.dumps(obj, indent=2).encode("utf-8")
    return json.dumps(obj, separators=(",", ":")).encode("utf-8")


def build_binary_case() -> PcapCase:
    flow = TcpFlow()
    flow.syn()
    _handshake(flow, pmd=False)

    single = b"BIN-SINGLE"
    frag_parts = [b"FRAG-A", b"FRAG-B", b"FRAG-C"]
    multi_a, multi_b = b"MSG-1", b"MSG-2"
    large = _audio_chunk(9, 300)

    # One message per TCP segment.
    flow.data(False, ws_frame(2, single))
    # A fragmented message spread over three TCP segments.
    flow.data(False, ws_frame(2, frag_parts[0], fin=False))
    flow.data(False, ws_frame(0, frag_parts[1], fin=False))
    flow.data(False, ws_frame(0, frag_parts[2], fin=True))
    # Two complete messages coalesced into one TCP segment.
    flow.data(False, ws_frame(2, multi_a) + ws_frame(2, multi_b))
    # Extended (16 bit) payload length.
    flow.data(False, ws_frame(2, large))

    # Opposite direction traffic must be filtered out.
    flow.data(True, ws_frame(2, b"C2S-DATA", mask=True))

    expected = single + b"".join(frag_parts) + multi_a + multi_b + large
    return PcapCase(
        name="binary",
        pcap=flow.to_pcap(),
        server_port=flow.server_port,
        client_port=flow.client_port,
        expected_binary=expected,
    )


def build_text_case() -> PcapCase:
    flow = TcpFlow()
    flow.syn()
    _handshake(flow, pmd=False)

    chunks = [_audio_chunk(1), _audio_chunk(2), _audio_chunk(3), _audio_chunk(4)]
    messages = [
        _text_audio_message(chunks[0], 1),
        _text_audio_message(chunks[1], 2, pretty=True),
        b'{"type":"control","op":"ping"}',
        _text_audio_message(chunks[2], 3),
    ]

    flow.data(False, ws_frame(1, messages[0]))
    flow.data(False, ws_frame(1, messages[1]))
    flow.data(False, ws_frame(1, messages[2]))
    # Two JSON messages in one TCP segment.
    flow.data(False, ws_frame(1, messages[3]) + ws_frame(1, _text_audio_message(chunks[3], 4)))
    # Opposite direction control traffic.
    flow.data(True, ws_frame(1, b'{"type":"client-control"}', mask=True))

    expected = b"".join(chunks)
    return PcapCase(
        name="text",
        pcap=flow.to_pcap(),
        server_port=flow.server_port,
        client_port=flow.client_port,
        expected_text_audio=expected,
        expected_text_messages=[
            json.loads(m) for m in messages
        ],
    )


def build_pmd_binary_case() -> PcapCase:
    flow = TcpFlow()
    flow.syn()
    _handshake(flow, pmd=True)

    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    chunks = [_audio_chunk(21), _audio_chunk(22), _audio_chunk(23)]
    for i, chunk in enumerate(chunks):
        payload = pmd_compress(compressor, chunk)
        flow.data(False, ws_frame(2, payload, rsv1=True))

    return PcapCase(
        name="pmd_binary",
        pcap=flow.to_pcap(),
        server_port=flow.server_port,
        client_port=flow.client_port,
        expected_binary=b"".join(chunks),
    )


def build_pmd_text_case() -> PcapCase:
    flow = TcpFlow()
    flow.syn()
    _handshake(flow, pmd=True)

    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    chunks = [_audio_chunk(31), _audio_chunk(32)]
    for i, chunk in enumerate(chunks):
        payload = pmd_compress(compressor, _text_audio_message(chunk, i + 1))
        flow.data(False, ws_frame(1, payload, rsv1=True))

    return PcapCase(
        name="pmd_text",
        pcap=flow.to_pcap(),
        server_port=flow.server_port,
        client_port=flow.client_port,
        expected_text_audio=b"".join(chunks),
    )


CASES = {
    "binary": build_binary_case,
    "text": build_text_case,
    "pmd_binary": build_pmd_binary_case,
    "pmd_text": build_pmd_text_case,
}


def build_case(name: str) -> PcapCase:
    return CASES[name]()


if __name__ == "__main__":
    import sys

    case_name = sys.argv[1] if len(sys.argv) > 1 else "binary"
    case = build_case(case_name)
    out = sys.argv[2] if len(sys.argv) > 2 else f"{case_name}.pcap"
    with open(out, "wb") as fh:
        fh.write(case.pcap)
    print(f"wrote {out}: {len(case.pcap)} bytes")
