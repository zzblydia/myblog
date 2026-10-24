# NFS 挂载卡死导致端口被占用：复现与两种解法

## 现象

客户端执行 `mount -t nfs 192.168.8.43:/u01 /u01` 时，因服务端不可达（ping 不通 / nfsd 未启动）
而长时间卡住。守护进程先监听本地 `20022` 端口再执行 mount，运维用 `killall` 杀掉它后重启，
新实例因端口被旧进程的子进程占用而 `bind` 失败：

```
[guard pid=10350] listen ok on 0.0.0.0:20022 (fd=3)
...
sudo killall mount_guard
sudo ./mount_guard
[guard pid=10446] bind(0.0.0.0:20022) failed: Address already in use
```

## 根因：fd 继承链

```
mount_guard (fd 3 → socket)
  └─ system() fork 的 sh ──exec──> timeout
        └─ fork ──> mount
              └─ fork ──> mount.nfs      ← 真正卡在 RPC 探测的进程
```

`fork()` 复制 fd 表，`exec()` 只在 fd 带 `FD_CLOEXEC` 时才关闭它。监听 socket 默认不带该标志，
于是 timeout / mount / mount.nfs 全都持有它；`killall` 只杀掉第一代，后两代仍让端口处于 LISTEN。

## 两种解法

| 方案 | 实现 | kill 后端口释放 |
|---|---|---|
| 方案 1 | 监听 fd 被子进程继承，mount 外包 `timeout -k 5 10` | 需等 timeout 到期（实测 6.5s） |
| 方案 2 | `socket(AF_INET, SOCK_STREAM \| SOCK_CLOEXEC, 0)` | 立即（实测 0.0s） |

两者职责不同：`timeout` 防挂载永久卡死，`SOCK_CLOEXEC` 让端口不被旧子进程拖着。
生产建议 **方案 2 + `timeout`**。

## 构建

```bash
# CMake（产出 mount_guard=方案2、mount_guard_tmo=方案1）
cmake -S . -B build && cmake --build build -j

# 或手工
gcc -std=c11 -O2 -Wall -Wextra -o mount_guard     mount_guard.c
gcc -std=c11 -O2 -Wall -Wextra -DUSE_CLOEXEC=0 -o mount_guard_tmo mount_guard.c
```

## 运行

```bash
sudo ./mount_guard          # 方案 2（默认），监听 20022 后执行真实 mount
sudo ./mount_guard_tmo      # 方案 1，对照用
sudo killall mount_guard    # 停止
```

关键参数为宏，改端口/挂载目标直接改 `mount_guard.c` 顶部：

```c
#define PORT        20022
#define MOUNT_CMD   "timeout -k 5 10 mount -t nfs 192.168.8.43:/u01 /u01"
#define USE_CLOEXEC 1
```

退出码：`2=socket` `3=bind`（端口被占）`4=listen`。

## 验证

必须 root（`mount.nfs` 需要 CAP_SYS_ADMIN），且被测服务端不可达。

```bash
make && sudo ./verify_real.sh     # 约 25 秒，产出 verify_real.log
```

脚本对两个二进制各跑一轮，记录端口持有者、mount 进程链、`killall` 后端口状态、
立即重启结果、端口释放耗时与残留进程。

### 实测结果（Linux 6.12 / util-linux 2.41，真实 mount 到不可达的 192.168.8.43）

| 指标 | 方案 1 | 方案 2 |
|---|---|---|
| 启动后端口持有者 | mount.nfs + mount + timeout + sh + guard | 仅 guard |
| `killall` 后 | 仍 LISTEN | 立即释放 |
| 立即重启 | `bind failed`，exit=3 | `listen ok`，成功 |
| 释放耗时 | 6.5s | 0.0s |

## 文件说明

| 文件 | 说明 |
|---|---|
| `mount_guard.c` | 单文件实现，`USE_CLOEXEC` 宏切换两种方案 |
| `CMakeLists.txt` | 同时构建两个 target |
| `verify_real.sh` | 真机自动验证脚本（需 root） |
| `CLAUDE.md` | 原理、实现步骤、已知坑的详细文档 |

## 已知坑

1. 非 root 执行 mount 会立即报错返回，复现不出卡死。
2. `pkill -f` 清理 mount 会命中执行者自己的命令行；按端口清理改用 `fuser -k -TERM 20022/tcp`。
3. `killall` 匹配 15 字符截断后的 comm，二进制名不要超过 15 字符；`mount` 与 `mount.nfs` 名字不同，需分别处理。

完整 7 条（含 `--foreground` 陷阱、叠层挂载、`rc=124` 语义、`-k` 兜底）见 `CLAUDE.md` §7。
