#!/usr/bin/env bash
# End-to-end verification with real Python WebSocket traffic.
#
# Every case starts the mock server, captures the loopback interface with
# tcpdump, runs the mock client, then feeds the pcap through both stages of the
# tool.  The decoded audio is compared byte-for-byte (sha256) with the bytes
# the peer actually sent.  Nothing is hand-crafted here: tcpdump sees the same
# packets a real deployment would produce.
#
# Usage:
#   tests/capture_e2e.sh          # run all cases and remove the work directory
#   KEEP=1 tests/capture_e2e.sh   # keep pcaps/payloads for debugging
#
# Requires: tshark, tcpdump, openssl, python3.  tcpdump must be able to capture
# on lo without interactive privileges (CAP_NET_RAW or a sudoers rule).

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PY=${PYTHON:-python3}
mkdir -p /tmp/opencode
WORK=$(mktemp -d /tmp/opencode/ws_e2e.XXXXXX)
SERVER_PID=""
TCPDUMP_PID=""
FAILURES=0
KEEP=${KEEP:-0}

CERT="$WORK/cert.pem"
KEY="$WORK/key.pem"


stop_tcpdump() {
    if [[ -n "${TCPDUMP_PID:-}" ]]; then
        kill -INT "$TCPDUMP_PID" 2>/dev/null || true
        wait "$TCPDUMP_PID" 2>/dev/null || true
        TCPDUMP_PID=""
    fi
}

stop_server() {
    if [[ -n "${SERVER_PID:-}" ]]; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
        SERVER_PID=""
    fi
}

cleanup() {
    stop_tcpdump
    stop_server
    if [[ "$KEEP" == "1" ]]; then
        printf 'artifacts kept in %s\n' "$WORK"
    else
        rm -rf "$WORK"
    fi
}
trap cleanup EXIT

require_tools() {
    local tool
    for tool in tshark tcpdump openssl "$PY"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            printf 'missing required tool: %s\n' "$tool" >&2
            exit 2
        fi
    done
}

# run_case NAME SERVER_CASE CLIENT_SEND DIRECTION TLS EXPECTED_SIDE TYPE
#   SERVER_CASE    binary|text|pmd_binary|pmd_text|none
#   CLIENT_SEND    none|binary|text|pmd_binary|pmd_text
#   DIRECTION      s2c|c2s
#   TLS            1 for TLS, 0 for cleartext
#   EXPECTED_SIDE  server|client (which peer writes expected.bin)
#   TYPE           binary|text (payload format)
run_case() {
    local name=$1 server_case=$2 client_send=$3 direction=$4
    local use_tls=$5 expected_side=$6 payload_type=$7

    local dir="$WORK/$name"
    mkdir -p "$dir"
    local port_file="$dir/port"
    local pcap="$dir/cap.pcap"
    local payload="$dir/capture.payload"
    local audio="$dir/audio.bin"
    local keylog="$dir/keys.log"
    local expected="$dir/expected.bin"

    local -a server_args=(--port-file "$port_file" --case "$server_case"
                          --hold 0.8 --no-log-file --log-level WARNING)
    local -a client_args=(--port-file "$port_file" --send "$client_send"
                          --no-log-file --log-level WARNING)

    if [[ "$use_tls" == "1" ]]; then
        server_args+=(--cert "$CERT" --key "$KEY" --keylog "$keylog")
        client_args+=(--tls --keylog "$keylog")
    fi
    if [[ "$expected_side" == "server" ]]; then
        server_args+=(--expected-out "$expected")
    else
        client_args+=(--expected-out "$expected")
    fi

    "$PY" "$ROOT/tests/mock_ws_server.py" "${server_args[@]}" &
    SERVER_PID=$!

    # The server binds port 0 and publishes the real port atomically.
    local i
    for i in $(seq 1 100); do
        [[ -s "$port_file" ]] && break
        sleep 0.05
    done
    if [[ ! -s "$port_file" ]]; then
        printf 'FAIL %-26s server did not publish a port\n' "$name"
        stop_server
        return 1
    fi
    local port
    port=$(cat "$port_file")

    tcpdump -i lo -U -s 0 -w "$pcap" "tcp port $port" \
        >"$dir/tcpdump.log" 2>&1 &
    TCPDUMP_PID=$!
    sleep 0.3

    if ! "$PY" "$ROOT/tests/mock_ws_client.py" "${client_args[@]}"; then
        printf 'FAIL %-26s client failed\n' "$name"
        stop_tcpdump
        stop_server
        return 1
    fi

    if ! wait "$SERVER_PID"; then
        printf 'FAIL %-26s server failed\n' "$name"
        SERVER_PID=""
        stop_tcpdump
        return 1
    fi
    SERVER_PID=""

    # Give tcpdump a moment to flush the last close frames, then stop it.
    sleep 0.2
    stop_tcpdump

    local -a dump_args=(--pcap "$pcap" --out "$payload" --type "$payload_type"
                        --direction "$direction" --no-log-file --log-level WARNING)
    if [[ "$use_tls" == "1" ]]; then
        dump_args+=(--keylog "$keylog")
    fi
    if ! "$PY" "$ROOT/ws_payload_dump.py" "${dump_args[@]}"; then
        printf 'FAIL %-26s extractor failed\n' "$name"
        return 1
    fi

    local -a decode_args=(--input "$payload" --out "$audio"
                          --no-log-file --log-level WARNING)
    if [[ "$payload_type" == "binary" ]]; then
        decode_args+=(--type binary)
    else
        decode_args+=(--type text --key audio)
    fi
    if ! "$PY" "$ROOT/ws_payload_decode.py" "${decode_args[@]}"; then
        printf 'FAIL %-26s decoder failed\n' "$name"
        return 1
    fi

    if [[ ! -f "$expected" ]]; then
        printf 'FAIL %-26s peer did not write the expected audio\n' "$name"
        return 1
    fi
    if [[ ! -f "$audio" ]]; then
        printf 'FAIL %-26s decoder did not produce an output file\n' "$name"
        return 1
    fi

    local expected_sha actual_sha
    expected_sha=$(sha256sum "$expected" | awk '{print $1}')
    actual_sha=$(sha256sum "$audio" | awk '{print $1}')
    if [[ "$expected_sha" != "$actual_sha" ]]; then
        printf 'FAIL %-26s audio mismatch expected=%s actual=%s\n' \
            "$name" "$expected_sha" "$actual_sha"
        return 1
    fi

    # Check the intermediate .payload contract as well: binary is a raw
    # concatenation, text is one complete JSON document per line.
    if [[ "$payload_type" == "binary" ]]; then
        if ! cmp -s "$payload" "$expected"; then
            printf 'FAIL %-26s binary payload is not the raw concatenation\n' "$name"
            return 1
        fi
    else
        if ! "$PY" - "$payload" <<'PYCHECK'
import json
import sys

lines = [line for line in open(sys.argv[1], encoding="utf-8") if line.strip()]
if not lines:
    raise SystemExit("empty text payload")
for line in lines:
    json.loads(line)
PYCHECK
        then
            printf 'FAIL %-26s text payload is not valid JSON Lines\n' "$name"
            return 1
        fi
    fi

    printf 'PASS %-26s %s/%s (%s bytes)\n' \
        "$name" "$direction" "$payload_type" "$(stat -c%s "$audio")"
}


require_tools
openssl req -x509 -newkey rsa:2048 -nodes -keyout "$KEY" -out "$CERT" \
    -days 1 -subj '/CN=localhost' >/dev/null 2>&1

# Cleartext, server to client.
run_case s2c_plain_binary   binary       none       s2c 0 server binary || FAILURES=$((FAILURES + 1))
run_case s2c_plain_text     text         none       s2c 0 server text   || FAILURES=$((FAILURES + 1))

# Cleartext, client to server (masked frames, including fragmentation).
run_case c2s_plain_binary   none         binary     c2s 0 client binary || FAILURES=$((FAILURES + 1))
run_case c2s_plain_text     none         text       c2s 0 client text   || FAILURES=$((FAILURES + 1))
run_case c2s_tls_binary     none         binary     c2s 1 client binary || FAILURES=$((FAILURES + 1))

# TLS, server to client.  The 101 response and the first frames are often
# coalesced into one TLS record, which is exactly the case the stream parser
# has to handle.
run_case s2c_tls_binary     binary       none       s2c 1 server binary || FAILURES=$((FAILURES + 1))
run_case s2c_tls_text       text         none       s2c 1 server text   || FAILURES=$((FAILURES + 1))

# permessage-deflate, cleartext and TLS.
run_case s2c_pmd_binary     pmd_binary   none       s2c 0 server binary || FAILURES=$((FAILURES + 1))
run_case s2c_pmd_text       pmd_text     none       s2c 0 server text   || FAILURES=$((FAILURES + 1))
run_case s2c_tls_pmd_binary pmd_binary   none       s2c 1 server binary || FAILURES=$((FAILURES + 1))

if (( FAILURES > 0 )); then
    printf '%d capture E2E case(s) failed\n' "$FAILURES"
    exit 1
fi
printf 'all capture E2E cases passed\n'
