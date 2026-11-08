#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Turn a .payload file produced by ws_payload_dump.py into one audio stream.

Binary payload file:
    The whole file is the concatenation of the WebSocket binary messages, so
    decoding is a validated copy (with optional WAV wrapping).

Text payload file:
    One complete JSON document per line.  The audio is stored in a JSON key
    (for example "audio") whose value is base64.  The key may be nested at any
    depth; use --key audio for a recursive name search or --key data.audio for
    an exact path.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import logging
import os
import re
import struct
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional, Sequence

LOG = logging.getLogger("ws_payload_decode")


class DecodeError(RuntimeError):
    """Raised for a user-visible decoding failure."""


_MISSING = object()
_PATH_TOKEN = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


# ---------------------------------------------------------------------------
# logging
# ---------------------------------------------------------------------------

def setup_logging(prog: str, log_file: Optional[str], level: str, no_file: bool) -> Optional[Path]:
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
# JSON key lookup
# ---------------------------------------------------------------------------

def parse_key_path(path: str) -> list[object]:
    """Parse "data.audio", "result.items[0].audio" or "a[0][1]"."""
    tokens: list[object] = []
    pos = 0
    while pos < len(path):
        if path[pos] == ".":
            pos += 1
            continue
        if path[pos] == "[":
            end = path.find("]", pos)
            if end < 0:
                raise DecodeError(f"invalid key path (unclosed '['): {path}")
            index = path[pos + 1:end]
            if not index.isdigit():
                raise DecodeError(f"invalid array index in key path: {path}")
            tokens.append(int(index))
            pos = end + 1
            continue
        match = _PATH_TOKEN.match(path, pos)
        if not match:
            raise DecodeError(f"invalid key path: {path}")
        tokens.append(match.group(1))
        pos = match.end()
    if not tokens:
        raise DecodeError(f"empty key path: {path}")
    return tokens


def resolve_key_path(document, tokens: Sequence[object]):
    current = document
    for token in tokens:
        if isinstance(token, int):
            if not isinstance(current, list) or token >= len(current):
                return _MISSING
            current = current[token]
        else:
            if not isinstance(current, dict) or token not in current:
                return _MISSING
            current = current[token]
    return current


def find_key_recursive(document, name: str) -> Iterator[object]:
    """Yield every value whose object key equals name, in document order."""
    if isinstance(document, dict):
        for key, value in document.items():
            if key == name:
                yield value
            yield from find_key_recursive(value, name)
    elif isinstance(document, list):
        for item in document:
            yield from find_key_recursive(item, name)


def iter_strings(value, context: str) -> Iterator[str]:
    """Flatten a JSON value into the strings that carry audio payloads."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item, context)
    else:
        LOG.warning("%s: key value is %s, not a string or list; skipped",
                    context, type(value).__name__)


# ---------------------------------------------------------------------------
# value decoding
# ---------------------------------------------------------------------------

def decode_base64(value: str) -> bytes:
    """Decode standard/urlsafe base64, with or without padding and data URI."""
    text = value.strip()
    if text.startswith("data:"):
        comma = text.find(",")
        if comma < 0:
            raise ValueError("data URI without comma")
        text = text[comma + 1:]
    text = "".join(text.split())
    # RFC 4648 section 5 alphabet is common in JSON generated by JavaScript.
    text = text.replace("-", "+").replace("_", "/")
    text += "=" * (-len(text) % 4)
    try:
        return base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"invalid base64: {exc}") from exc


def decode_value(value: str, encoding: str) -> bytes:
    if encoding == "raw":
        return value.encode("utf-8")
    return decode_base64(value)


# ---------------------------------------------------------------------------
# output helpers
# ---------------------------------------------------------------------------

def wav_header(data_length: int, rate: int, channels: int, bits: int) -> bytes:
    if bits % 8:
        raise DecodeError("WAV sample width must be a multiple of 8 bits")
    if data_length > 0xFFFFFFFF - 36:
        raise DecodeError("WAV output would exceed the 4 GiB RIFF limit")
    block_align = channels * bits // 8
    byte_rate = rate * block_align
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_length, b"WAVE",
        b"fmt ", 16, 1, channels, rate, byte_rate, block_align, bits,
        b"data", data_length,
    )


class AtomicOutput:
    """Write to a hidden temp file and rename only after a full success."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.tmp_path = path.with_name(path.name + f".tmp.{os.getpid()}")
        self.handle = open(self.tmp_path, "wb")
        self.bytes_written = 0

    def write(self, data: bytes) -> None:
        self.handle.write(data)
        self.bytes_written += len(data)

    def commit(self) -> None:
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.handle.close()
        os.chmod(self.tmp_path, 0o600)
        self.tmp_path.replace(self.path)

    def abort(self) -> None:
        try:
            self.handle.close()
        except OSError:
            pass
        try:
            self.tmp_path.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# decode operations
# ---------------------------------------------------------------------------

@dataclass
class DecodeStats:
    payload_type: str
    messages: int = 0
    matched: int = 0
    skipped: int = 0
    bytes_written: int = 0
    sha256: str = ""
    out_path: str = ""


def _hash_and_write(output: AtomicOutput, data: bytes, digest) -> None:
    output.write(data)
    digest.update(data)


def decode_binary(input_path: Path, out_path: Path, *, wav: bool,
                  rate: int, channels: int, bits: int) -> DecodeStats:
    """The binary .payload already is the merged stream."""
    stats = DecodeStats(payload_type="binary", out_path=str(out_path))
    digest = hashlib.sha256()
    source_size = input_path.stat().st_size
    if source_size == 0:
        raise DecodeError(f"input payload is empty: {input_path}")

    output = AtomicOutput(out_path)
    try:
        if wav:
            output.write(b"\x00" * 44)  # reserve the header, patched below
        with open(input_path, "rb") as source:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                _hash_and_write(output, chunk, digest)
        if wav:
            header = wav_header(output.bytes_written - 44, rate, channels, bits)
            output.handle.seek(0)
            output.handle.write(header)
            output.handle.seek(0, os.SEEK_END)
        stats.bytes_written = output.bytes_written - (44 if wav else 0)
        stats.messages = 1
        stats.matched = 1
        stats.sha256 = digest.hexdigest()
        output.commit()
    except BaseException:
        output.abort()
        raise
    return stats


def decode_text(input_path: Path, out_path: Path, *, key: str,
                value_encoding: str, invalid_json: str, wav: bool,
                rate: int, channels: int, bits: int) -> DecodeStats:
    """Extract a JSON key from every line and merge the decoded values."""
    stats = DecodeStats(payload_type="text", out_path=str(out_path))
    digest = hashlib.sha256()
    tokens = parse_key_path(key) if ("." in key or "[" in key) else None
    output = AtomicOutput(out_path)

    try:
        with open(input_path, "r", encoding="utf-8", errors="strict") as source:
            for line_number, line in enumerate(source, 1):
                line = line.strip()
                if not line:
                    continue
                stats.messages += 1
                try:
                    document = json.loads(line)
                except json.JSONDecodeError as exc:
                    if invalid_json == "skip":
                        LOG.warning("line %d: invalid JSON skipped: %s", line_number, exc)
                        stats.skipped += 1
                        continue
                    raise DecodeError(f"line {line_number}: invalid JSON: {exc}") from exc

                if tokens is not None:
                    value = resolve_key_path(document, tokens)
                    values = [] if value is _MISSING else [value]
                else:
                    values = list(find_key_recursive(document, key))

                if not values:
                    LOG.debug("line %d: key %r not present; skipped", line_number, key)
                    stats.skipped += 1
                    continue

                matched_here = 0
                for value in values:
                    for string in iter_strings(value, f"line {line_number}"):
                        try:
                            chunk = decode_value(string, value_encoding)
                        except ValueError as exc:
                            raise DecodeError(f"line {line_number}: {exc}") from exc
                        if not chunk:
                            continue
                        if wav and output.bytes_written == 0:
                            output.write(b"\x00" * 44)
                        _hash_and_write(output, chunk, digest)
                        matched_here += 1

                if matched_here == 0:
                    LOG.debug("line %d: key %r had no usable value", line_number, key)
                    stats.skipped += 1
                    continue
                stats.matched += 1

        if stats.matched == 0:
            raise DecodeError(f"no message contained a usable key {key!r}")

        if wav:
            header = wav_header(output.bytes_written - 44, rate, channels, bits)
            output.handle.seek(0)
            output.handle.write(header)
            output.handle.seek(0, os.SEEK_END)
        stats.bytes_written = output.bytes_written - (44 if wav else 0)
        stats.sha256 = digest.hexdigest()
        output.commit()
    except BaseException:
        output.abort()
        raise
    return stats


def list_keys(input_path: Path) -> int:
    """Print the JSON key paths seen in a text payload file."""
    counts: dict[str, int] = {}

    def walk(node, prefix: str) -> None:
        if isinstance(node, dict):
            for name, value in node.items():
                path = f"{prefix}.{name}" if prefix else name
                counts[path] = counts.get(path, 0) + 1
                walk(value, path)
        elif isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{prefix}[{index}]")

    with open(input_path, "r", encoding="utf-8", errors="strict") as source:
        for line_number, line in enumerate(source, 1):
            line = line.strip()
            if not line:
                continue
            try:
                walk(json.loads(line), "")
            except json.JSONDecodeError as exc:
                LOG.warning("line %d: invalid JSON: %s", line_number, exc)
    for path, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"{count:6d}  {path}")
    return 0


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------

def run_selftest() -> int:
    failures = 0
    chunk1 = b"audio-one"
    chunk2 = b"audio-two"
    chunk3 = b"audio-three"
    chunk4 = b"audio-four"

    def b64(data: bytes, urlsafe: bool = False, pad: bool = True) -> str:
        text = base64.urlsafe_b64encode(data).decode() if urlsafe else base64.b64encode(data).decode()
        return text if pad else text.rstrip("=")

    with tempfile.TemporaryDirectory(prefix="ws_decode_selftest_") as tmpdir:
        tmp = Path(tmpdir)

        # --- binary -------------------------------------------------------
        payload = tmp / "binary.payload"
        expected = chunk1 + chunk2 + chunk3
        payload.write_bytes(expected)
        out = tmp / "binary.out"
        stats = decode_binary(payload, out, wav=False, rate=16000,
                              channels=1, bits=16)
        if out.read_bytes() != expected or stats.sha256 != hashlib.sha256(expected).hexdigest():
            LOG.error("selftest binary FAILED")
            failures += 1
        else:
            LOG.info("selftest binary OK")

        # --- binary + WAV -------------------------------------------------
        out = tmp / "binary.wav"
        decode_binary(payload, out, wav=True, rate=16000, channels=1, bits=16)
        data = out.read_bytes()
        if data[:4] != b"RIFF" or data[8:12] != b"WAVE" or data[44:] != expected:
            LOG.error("selftest wav FAILED")
            failures += 1
        else:
            LOG.info("selftest wav OK")

        # --- text: nested key, urlsafe, missing padding, array, control ---
        lines = [
            json.dumps({"type": "audio", "data": {"audio": b64(chunk1)}},
                       separators=(",", ":")),
            json.dumps({"audio": b64(chunk2, urlsafe=True, pad=False)},
                       separators=(",", ":")),
            json.dumps({"audio": [b64(chunk3), b64(chunk4)]},
                       separators=(",", ":")),
            json.dumps({"type": "control"}, separators=(",", ":")),
        ]
        text_payload = tmp / "text.payload"
        text_payload.write_text("\n".join(lines) + "\n", encoding="utf-8")
        expected = chunk1 + chunk2 + chunk3 + chunk4

        out = tmp / "text.recursive.out"
        stats = decode_text(text_payload, out, key="audio", value_encoding="base64",
                            invalid_json="error", wav=False, rate=16000,
                            channels=1, bits=16)
        if out.read_bytes() != expected or stats.matched != 3:
            LOG.error("selftest text recursive FAILED: %d bytes", out.stat().st_size)
            failures += 1
        else:
            LOG.info("selftest text recursive OK")

        out = tmp / "text.path.out"
        decode_text(text_payload, out, key="data.audio", value_encoding="base64",
                    invalid_json="error", wav=False, rate=16000, channels=1, bits=16)
        if out.read_bytes() != chunk1:
            LOG.error("selftest text path FAILED")
            failures += 1
        else:
            LOG.info("selftest text path OK")

        # --- raw value encoding ------------------------------------------
        raw_payload = tmp / "raw.payload"
        raw_payload.write_text(json.dumps({"audio": "raw-bytes"}) + "\n", encoding="utf-8")
        out = tmp / "raw.out"
        decode_text(raw_payload, out, key="audio", value_encoding="raw",
                    invalid_json="error", wav=False, rate=16000, channels=1, bits=16)
        if out.read_bytes() != b"raw-bytes":
            LOG.error("selftest raw FAILED")
            failures += 1
        else:
            LOG.info("selftest raw OK")

        # --- invalid JSON skip -------------------------------------------
        bad_payload = tmp / "bad.payload"
        bad_payload.write_text("{not-json}\n" + lines[0] + "\n", encoding="utf-8")
        out = tmp / "bad.out"
        try:
            decode_text(bad_payload, out, key="audio", value_encoding="base64",
                        invalid_json="skip", wav=False, rate=16000, channels=1, bits=16)
            if out.read_bytes() != chunk1:
                LOG.error("selftest invalid-json skip FAILED")
                failures += 1
            else:
                LOG.info("selftest invalid-json skip OK")
        except DecodeError as exc:
            LOG.error("selftest invalid-json skip FAILED: %s", exc)
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
        description="Decode a ws_payload_dump.py .payload file into one audio stream.",
    )
    parser.add_argument("--input", help="input .payload file")
    parser.add_argument("--out", help="output audio file")
    parser.add_argument("--type", choices=("binary", "text"), help="payload type")
    parser.add_argument("--key", help="JSON key name (recursive) or path (data.audio)")
    parser.add_argument("--value-encoding", choices=("base64", "raw"), default="base64",
                        help="how the JSON value stores audio bytes (default base64)")
    parser.add_argument("--invalid-json", choices=("error", "skip"), default="error",
                        help="behaviour for malformed JSON lines")
    parser.add_argument("--wav", action="store_true", help="wrap raw PCM in a WAV header")
    parser.add_argument("--rate", type=int, default=16000, help="WAV sample rate")
    parser.add_argument("--channels", type=int, default=1, help="WAV channels")
    parser.add_argument("--bits", type=int, default=16, help="WAV bits per sample")
    parser.add_argument("--list-keys", action="store_true",
                        help="list JSON key paths found in the input and exit")
    parser.add_argument("--selftest", action="store_true", help="run built-in tests")
    parser.add_argument("--log-file", help="log path (default: <prog>_<timestamp>.log)")
    parser.add_argument("--log-level", default="INFO",
                        help="DEBUG/INFO/WARNING/ERROR (default INFO)")
    parser.add_argument("--no-log-file", action="store_true", help="console logging only")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging("ws_payload_decode", args.log_file, args.log_level, args.no_log_file)

    try:
        if args.selftest:
            return run_selftest()

        if not args.input:
            parser.error("--input is required")
        if not args.out and not args.list_keys:
            parser.error("--out is required unless --list-keys is used")
        if not args.type and not args.list_keys:
            parser.error("--type is required")
        if not Path(args.input).exists():
            raise DecodeError(f"input not found: {args.input}")

        if args.list_keys:
            return list_keys(Path(args.input))

        if args.wav:
            if args.rate <= 0 or args.channels <= 0 or args.bits <= 0:
                raise DecodeError("--rate, --channels and --bits must be positive")

        if args.type == "binary":
            stats = decode_binary(
                Path(args.input), Path(args.out), wav=args.wav,
                rate=args.rate, channels=args.channels, bits=args.bits,
            )
        else:
            if not args.key:
                parser.error("--key is required for --type text")
            stats = decode_text(
                Path(args.input), Path(args.out), key=args.key,
                value_encoding=args.value_encoding,
                invalid_json=args.invalid_json,
                wav=args.wav, rate=args.rate, channels=args.channels, bits=args.bits,
            )

        LOG.info("summary: type=%s messages=%d matched=%d skipped=%d bytes=%d sha256=%s out=%s",
                 stats.payload_type, stats.messages, stats.matched, stats.skipped,
                 stats.bytes_written, stats.sha256, stats.out_path)
        if args.wav and args.rate and args.bits and args.channels:
            block = args.channels * args.bits // 8
            if block:
                LOG.info("duration: %.3f seconds", stats.bytes_written / (args.rate * block))
        return 0
    except DecodeError as exc:
        LOG.error("%s", exc)
        return 2
    except UnicodeDecodeError as exc:
        LOG.error("input is not valid UTF-8: %s", exc)
        return 2
    except KeyboardInterrupt:
        LOG.warning("interrupted")
        return 130
    except OSError as exc:
        LOG.error("I/O error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
