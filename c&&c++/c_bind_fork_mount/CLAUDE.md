# CLAUDE.md

> 面向维护者/Agent 的工程文档。使用说明、实测对比见 `README.md`，本文不重复。

## 1. 目标

在服务端不可达时，让 `mount -t nfs 192.168.8.43:/u01 /u01` 卡住带来的“端口被子进程占用、
新实例无法启动”问题可复现、可验证、可根治。现象与失败输出见 `README.md`「现象」。

## 2. 原理补充（README 只给了进程链图，这里给判定规则）

- 端口能否被绑定，唯一取决于该 socket 的 **fd 引用计数是否归零**，与进程名、进程树层级无关。
- `fork()` 复制 fd 表；`exec()` 只在 fd 带 `FD_CLOEXEC` 时才关闭它。监听 socket 默认不带，
  所以 timeout / mount / mount.nfs 全部持有。
- coreutils `timeout` 默认 `setpgid` 自建进程组，到期对**整组**发信号（这也是 `--foreground`
  存在的原因：加上它子孙进程就不被计时）。因此方案 1 的端口释放时刻 = timeout 到期时刻，
  而不是 kill 时刻。

## 3. 两方案的关键差异

- 方案 1（`USE_CLOEXEC=0`）：保留原故障现象；`killall` 后仍需等 timeout 到期，存在固定失败窗口。
- 方案 2（`USE_CLOEXEC=1`）：`SOCK_CLOEXEC` 只在 `exec` 时生效，`fork → exec` 之间有微秒级窗口，
  可忽略；此后端口只归守护进程。
- 二者职责分离，建议同时启用：`timeout` 管“挂载不会永久卡死”，`SOCK_CLOEXEC` 管“端口不被拖着”。

## 4. 实现约束

- 单文件 `mount_guard.c`，文件顶部三个宏即全部可调参数：`PORT`、`MOUNT_CMD`、`USE_CLOEXEC`。
  改端口或挂载目标只改宏，不引入 argv 解析。
- `-DPORT=` 仅用于同机换端口验证（避免与已运行实例冲突），默认值仍是 20022。
- `CMakeLists.txt` 一次产出两个 target：`mount_guard`（方案 2）、`mount_guard_tmo`（方案 1）。
  构建与运行命令见 `README.md`。
- 监听失败即退出，不做重试；退出码由 `die()` 传入，供脚本判断（`2=socket 3=bind 4=listen`）。

## 5. 验证

### 5.1 前置条件

- 必须以 root 运行（`mount.nfs` 需要 CAP_SYS_ADMIN；非 root 会立即报
  `failed to apply fstab options` 或 `only root can do that`，复现不出卡死）。
- `192.168.8.43` 不可达，`/u01` 挂载点存在。
- 端口 20022 空闲：`ss -ltn 'sport = :20022'` 无输出。

### 5.2 一键验证

```bash
sudo ./verify_real.sh        # 约 25 秒, 产物 verify_real.log 及 case*.log
```

脚本对两个二进制各跑一轮，按序记录：端口持有者 → mount 进程链 → `killall` 后端口状态 →
立即重启结果 → 端口释放耗时 → 残留进程。`timeout -k 5 10` 保证每轮 mount 最多 15 秒。

### 5.3 手工逐步（判据）

方案 2：启动后 `ss` 只应看到 `mount_guard`；`killall` 后端口立即消失；立即重启 `listen ok`。
方案 1：启动后可见 `mount_guard_tmo + mount + mount.nfs`；`killall` 后前两者仍持有；
立即重启 `bind failed`（exit=3）；等 10s（+5s 兜底）后再启动才成功。

## 6. 实测原始记录

采集方式：`sudo ./verify_real.sh`（真实 mount 到不可达的 192.168.8.43）。
环境：Linux 6.12.94+deb13-amd64 / util-linux 2.41 / 端口 20022。

```
# 方案 1
[11:44:52] 启动           guard pid=11730 listen ok, fd=3
[11:44:54] 持有者         mount.nfs(11735) + mount(11734) + timeout(11733) + sh(11732) + guard(11730)
[11:44:54] killall        mount_guard_tmo
[11:44:54] kill 后        mount.nfs + mount + timeout + sh 仍持有 → 端口仍被占用
[11:44:54] 立即重启       bind failed: Address already in use → 失败
[11:45:02] 端口释放       kill 后 6.5s（timeout 10s 到期，整组被杀）
[11:45:02] 最终残留       无

# 方案 2
[11:45:02] 启动           guard pid=11894 listen ok, fd=3
[11:45:04] 持有者         仅 mount_guard(11894)；sh/timeout/mount 在链上但不持 fd
[11:45:04] killall        mount_guard
[11:45:05] kill 后        端口已释放
[11:45:05] 立即重启       guard pid=11924 listen ok → 成功
[11:45:06] 端口释放       kill 后 0.0s
[11:45:15] 最终残留       无（旧 timeout 链 ≤15s 自行退出）
```

结论：方案 1 只能把“长时间随机占用”压成“≤timeout 的确定窗口”；方案 2 毫秒级释放，重启必成功。

## 7. 已知坑

1. `timeout --foreground` 会让 mount/mount.nfs 逃出进程组，方案 1 直接失效，禁止使用。
2. `pkill -f 'mount -t nfs ...'` 会匹配到执行者自己的命令行，可能自杀；按端口清理用 `fuser -k -TERM 20022/tcp`。
3. `killall` 匹配 15 字符截断后的 comm，二进制名不要超过 15 字符；`mount.nfs` 与 `mount` 名字不同，需分别处理。
4. 真实 mount 必须 root 执行，否则立即报错返回，无法复现卡死。
5. 本机 `/u01` 已挂载 `192.168.8.42:/u01`；按需改 `MOUNT_CMD` 中的挂载点（如 `/mnt/test43`），避免叠层挂载。
6. `system()` 返回 124 表示 timeout 到期，日志需单独识别，不能当作 mount 自身错误。
7. `timeout` 到期只保证 mount/mount.nfs 被 TERM，若进程卡在不可中断状态需靠 `-k` 的 SIGKILL 兜底。

## 8. 待办

- 如需“端口占用可视化”，可在方案 1 下增加子进程 pid 打印。
- 方案 2 下若仍希望挂载失败后清理残留 `mount.nfs`，可加 `fuser -k -TERM 20022/tcp` 兜底（实测并无必要）。
