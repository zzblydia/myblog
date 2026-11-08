#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small WebSocket helpers shared by the mock server and client.

Only the standard library is used.  The implementation is intentionally
minimal: enough to drive a real TCP/TLS session so that tcpdump + tshark can
be tested with genuine packets instead of hand-built pcap records.
"""

from __future__ import annotations

import base64
import hashlib
import os
import socket
import ssl
import struct
import zlib
from typing import Optional

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


# ---------------------------------------------------------------------------
# HTTP upgrade
# ---------------------------------------------------------------------------

def read_until(sock: socket.socket, marker: bytes, limit: int = 65536) -> bytes:
    data = bytearray()
    while marker not in data:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("peer closed during HTTP handshake")
        data.extend(chunk)
        if len(data) > limit:
            raise ConnectionError("HTTP handshake too large")
    return bytes(data)


def parse_headers(raw: bytes) -> dict[str, str]:
    lines = raw.split(b"\r\n")
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if not line:
            continue
        name, _, value = line.partition(b":")
        if not _:
            continue
        headers[name.decode("latin-1").strip().lower()] = value.decode("latin-1").strip()
    return headers


def ws_accept(key: str) -> str:
    return base64.b64encode(hashlib.sha1((key + WS_GUID).encode()).digest()).decode()


def server_handshake(sock: socket.socket, allow_pmd: bool) -> dict[str, object]:
    raw = read_until(sock, b"\r\n\r\n")
    headers = parse_headers(raw)
    key = headers.get("sec-websocket-key")
    if not key:
        raise ConnectionError("client did not send Sec-WebSocket-Key")

    offered = "permessage-deflate" in headers.get("sec-websocket-extensions", "")
    use_pmd = allow_pmd and offered

    response = [
        "HTTP/1.1 101 Switching Protocols",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Accept: {ws_accept(key)}",
    ]
    if use_pmd:
        response.append("Sec-WebSocket-Extensions: permessage-deflate")
    response.append("")
    response.append("")
    sock.sendall("\r\n".join(response).encode("latin-1"))
    return {"pmd": use_pmd}


def client_handshake(sock: socket.socket, *, pmd: bool) -> dict[str, object]:
    key = base64.b64encode(os.urandom(16)).decode()
    request = [
        "GET /ws HTTP/1.1",
        "Host: localhost",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Key: {key}",
        "Sec-WebSocket-Version: 13",
    ]
    if pmd:
        request.append("Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits")
    request.append("")
    request.append("")
    sock.sendall("\r\n".join(request).encode("latin-1"))

    raw = read_until(sock, b"\r\n\r\n")
    headers = parse_headers(raw)
    status = raw.split(b"\r\n", 1)[0].decode("latin-1")
    if "101" not in status:
        raise ConnectionError(f"unexpected handshake status: {status}")
    if headers.get("sec-websocket-accept") != ws_accept(key):
        raise ConnectionError("bad Sec-WebSocket-Accept")
    return {"pmd": pmd and "permessage-deflate" in headers.get("sec-websocket-extensions", "")}


# ---------------------------------------------------------------------------
# TLS
# ---------------------------------------------------------------------------

def make_server_context(cert: str, key: str, keylog: Optional[str]) -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    # ALPN helps Wireshark pick the HTTP dissector inside a decrypted TLS flow.
    context.set_alpn_protocols(["http/1.1"])
    if keylog:
        context.keylog_filename = keylog
    return context


def make_client_context(keylog: Optional[str]) -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.set_alpn_protocols(["http/1.1"])
    if keylog:
        context.keylog_filename = keylog
    return context


# ---------------------------------------------------------------------------
# WebSocket frames
# ---------------------------------------------------------------------------

def frame_bytes(opcode: int, payload: bytes, *, fin: bool = True,
                rsv1: bool = False, mask: bool = False,
                mask_key: Optional[bytes] = None) -> bytes:
    """Encode one WebSocket frame into bytes."""
    b0 = (0x80 if fin else 0) | (0x40 if rsv1 else 0) | opcode
    length = len(payload)
    mask_bit = 0x80 if mask else 0
    if length < 126:
        header = bytes([b0, mask_bit | length])
    elif length < 65536:
        header = bytes([b0, mask_bit | 126]) + struct.pack("!H", length)
    else:
        header = bytes([b0, mask_bit | 127]) + struct.pack("!Q", length)

    if mask:
        key = mask_key or os.urandom(4)
        body = bytes(c ^ key[i % 4] for i, c in enumerate(payload))
        return header + key + body
    return header + payload


def send_frame(sock: socket.socket, opcode: int, payload: bytes, *,
               fin: bool = True, rsv1: bool = False, mask: bool = False) -> None:
    sock.sendall(frame_bytes(opcode, payload, fin=fin, rsv1=rsv1, mask=mask))


def recv_exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("peer closed")
        data.extend(chunk)
    return bytes(data)


def recv_frame(sock: socket.socket) -> tuple[bool, int, bool, bytes]:
    b0, b1 = recv_exact(sock, 2)
    fin = bool(b0 & 0x80)
    rsv1 = bool(b0 & 0x40)
    opcode = b0 & 0x0F
    masked = bool(b1 & 0x80)
    length = b1 & 0x7F
    if length == 126:
        length = struct.unpack("!H", recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", recv_exact(sock, 8))[0]
    key = recv_exact(sock, 4) if masked else b""
    payload = recv_exact(sock, length)
    if masked:
        payload = bytes(c ^ key[i % 4] for i, c in enumerate(payload))
    return fin, opcode, rsv1, payload


def drain_frames(sock: socket.socket, idle_timeout: float = 1.0) -> None:
    """Read until close, answering ping frames, with an idle timeout."""
    sock.settimeout(idle_timeout)
    try:
        while True:
            fin, opcode, rsv1, payload = recv_frame(sock)
            if opcode == 0x9:  # ping
                send_frame(sock, 0xA, payload)
            elif opcode == 0x8:  # close
                send_frame(sock, 0x8, b"")
                return
    except (socket.timeout, ConnectionError, OSError):
        return


# ---------------------------------------------------------------------------
# payload helpers
# ---------------------------------------------------------------------------

def audio_chunk(seed: int, size: int = 96) -> bytes:
    # Deterministic bytes containing 0x00 and 0x0a on purpose.
    return bytes(((seed * 37 + i * 11) & 0xFF) for i in range(size))


def pmd_compress(compressor: zlib.Compress, data: bytes) -> bytes:
    return compressor.compress(data) + compressor.flush(zlib.Z_SYNC_FLUSH)[:-4]


def write_expected(path: str, data: bytes) -> None:
    with open(path, "wb") as handle:
        handle.write(data)
