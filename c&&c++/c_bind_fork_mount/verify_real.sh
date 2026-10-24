#!/bin/bash
# verify_real.sh - 用真实 mount 验证两种方案的端口释放行为(必须 root)
#
# 用法: sudo ./verify_real.sh [端口]
# 产物: verify_real.log / case1.log / case1.restart.log / case2.log / case2.restart.log
# 依赖: mount_guard(方案2) 与 mount_guard_tmo(方案1) 已编译, 端口默认 20022

set -u

PORT="${1:-20022}"
HERE="$(cd "$(dirname "$0")" && pwd)"
LOG="$HERE/verify_real.log"
WINDOW=30                                   # 方案1 等待端口释放的上限(秒), 需 >= timeout 10+5

if [ "$(id -u)" -ne 0 ]; then
    echo "必须 root 运行: sudo $0 [端口]" >&2
    exit 1
fi

for b in mount_guard mount_guard_tmo; do
    [ -x "$HERE/$b" ] || { echo "缺少可执行文件 $b, 请先 make" >&2; exit 1; }
done

exec > >(tee "$LOG") 2>&1                   # 同时输出到屏幕和日志

ts()      { date '+%H:%M:%S.%3N'; }
say()     { echo "[$(ts)] $*"; }
holders() { ss -ltnp "sport = :$PORT" 2>/dev/null | tail -n +2; }
busy()    { ss -ltn "sport = :$PORT" 2>/dev/null | grep -q ":$PORT"; }
mnt_procs() { pgrep -af 'mount -t nfs 192\.168\.8\.43' 2>/dev/null; }
chains()  { pgrep -af 'mount -t nfs 192\.168\.8\.43|timeout -k 5 10 mount' 2>/dev/null; }

# 等上一轮的 mount 链彻底消失, 保证每一轮的证据干净
wait_chain_gone() {
    local n=0
    while chains > /dev/null 2>&1; do
        n=$((n + 1))
        [ $n -gt 100 ] && return 1
        sleep 0.2
    done
    return 0
}

cleanup() {
    killall mount_guard     2>/dev/null
    killall mount_guard_tmo 2>/dev/null
}
trap cleanup EXIT

echo "================= 环境 ==================="
say "host:   $(uname -srm)"
say "mount:  $(command -v mount) / $(mount --version 2>/dev/null | head -1)"
say "target: 192.168.8.43:/u01 -> /u01"
say "port:   $PORT"
if busy; then
    say "端口已被占用, 请先释放后重跑:"; holders; exit 1
fi
say "端口空闲, 开始验证"
echo

run_case() {
    local name=$1 bin=$2
    echo "================= $name ================="
    wait_chain_gone
    busy && { say "端口仍被占用, 跳过"; return 1; }

    say "1) 启动 $bin"
    setsid "$HERE/$bin" > "$HERE/$name.log" 2>&1 &
    sleep 2
    sed 's/^/     │ /' "$HERE/$name.log"
    say "2) 端口持有者:"; holders | sed 's/^/     │ /'
    say "3) mount 进程链:"; chains | sed 's/^/     │ /'

    say "4) killall $bin"
    killall "$bin"; sleep 0.3
    say "5) kill 后端口持有者:"; holders | sed 's/^/     │ /'
    if busy; then say "   >>> 端口仍被占用"; else say "   >>> 端口已释放"; fi

    say "6) 立即重启 $bin"
    setsid "$HERE/$bin" > "$HERE/$name.restart.log" 2>&1 &
    sleep 1
    sed 's/^/     │ /' "$HERE/$name.restart.log"
    if pgrep -f "$HERE/$bin" > /dev/null 2>&1; then
        say "     │ >>> 重启成功(进程存活)"
    else
        say "     │ >>> 重启失败(进程已退出)"
    fi
    killall "$bin" 2>/dev/null; sleep 0.3

    local t0
    t0=$(date +%s.%N)
    local n=0
    while busy; do
        n=$((n + 1))
        [ $n -gt $((WINDOW * 5)) ] && break
        sleep 0.2
    done
    if busy; then
        say "7) 等待 ${WINDOW}s 后端口仍未释放"
    else
        awk -v a="$t0" -v b="$(date +%s.%N)" \
            'BEGIN{printf "[%s] 7) 端口释放, kill 后总耗时: %.1fs\n", strftime("%H:%M:%S"), b-a}'
    fi
    # 等重启实例残留的 timeout 链自然退出(≤15s), 它不占端口, 只为让"残留"一栏干净
    wait_chain_gone
    say "8) 最终残留 mount 进程:"; mnt_procs | sed 's/^/     │ /' || true
    [ -z "$(mnt_procs)" ] && say "     │ 无"
    echo
}

run_case case1 mount_guard_tmo
run_case case2 mount_guard

echo "================= 汇总 ==================="
say "case1(方案1 USE_CLOEXEC=0): 见 case1.log, 关键看第 5 步是否仍被占用、第 7 步释放耗时"
say "case2(方案2 USE_CLOEXEC=1): 见 case2.log, 关键看第 5 步是否立即释放"
say "完整记录: $LOG"
