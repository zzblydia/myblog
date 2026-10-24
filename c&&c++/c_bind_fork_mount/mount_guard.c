// mount_guard.c - NFS 挂载卡死时"端口被子进程占用"的两种解法
//
// 方案 1 (-DUSE_CLOEXEC=0): fd 被子进程继承, 靠 timeout 到期杀整组回收端口
// 方案 2 (-DUSE_CLOEXEC=1): fd 带 SOCK_CLOEXEC, 端口只归本进程(默认)
// 编译与运行命令见 README.md, 工程细节见 CLAUDE.md

#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/wait.h>

#ifndef PORT
#define PORT        20022                   // 监听端口, 写死; -DPORT=xxxx 仅供本机换端口验证
#endif
#define MOUNT_CMD   "timeout -k 5 10 mount -t nfs 192.168.8.43:/u01 /u01"
                                            // -k 5: TERM 后 5 秒仍未退则整组 KILL

#ifndef USE_CLOEXEC
#define USE_CLOEXEC 1                       // 默认走方案 2
#endif

// 统一错误退出: 打印失败的系统调用名与 errno 文本, 不做重试, 由外部决定是否重启
static void die(const char *what, int code)
{
    fprintf(stderr, "[guard] %s failed: %s\n", what, strerror(errno));
    exit(code);
}

int main(void)
{
    struct sockaddr_in addr;
    int fd;
    int type = SOCK_STREAM;                 // 方案 1 用裸 SOCK_STREAM, 子进程可继承
    int rc;                                 // system() 的原始返回状态

    setvbuf(stdout, NULL, _IOLBF, 0);       // 行缓冲, 被 kill 前日志不丢

    // SOCK_CLOEXEC 要到 exec 时才关闭 fd, 因此挡住的是 exec 之后的 mount / mount.nfs
#if USE_CLOEXEC
    type |= SOCK_CLOEXEC;                   // 方案 2: exec 后子进程不再持有该 fd
#endif

    fd = socket(AF_INET, type, 0);
    if (fd < 0) die("socket", 2);

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(PORT);
    addr.sin_addr.s_addr = htonl(INADDR_ANY);   // 监听所有网卡

    // 不设 SO_REUSEADDR: 对活跃的 LISTEN socket 无效, 留着只会掩盖"端口被占"的事实
    // 只 bind + listen 不 accept: LISTEN 状态本身即占用端口
    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) die("bind", 3);
    if (listen(fd, 8) != 0) die("listen", 4);

    // 打印 fd 号, 便于与 ss / lsof 的输出对照
    printf("[guard pid=%d] listen ok on 0.0.0.0:%d, fd=%d\n",
           (int)getpid(), PORT, fd);

    // 服务端不可达时 system() 会阻塞, timeout 到期后 mount 及其子进程被整组杀掉;
    // 方案 1 下 mount / mount.nfs 已继承 fd, 所以端口要等这一步执行完才可能释放
    rc = system(MOUNT_CMD);
    if (rc == -1) {
        printf("[guard] system failed: %s\n", strerror(errno));
    } else if (WIFEXITED(rc) && WEXITSTATUS(rc) == 124) {
        printf("[guard] mount timeout (rc=124)\n");
    } else if (WIFEXITED(rc)) {
        printf("[guard] mount exited, status=%d\n", WEXITSTATUS(rc));
    } else if (WIFSIGNALED(rc)) {
        printf("[guard] mount killed by signal %d\n", WTERMSIG(rc));
    }

    // mount 已返回, 进程继续持有 fd, 留出"新旧两代并存"的观测窗口
    printf("[guard] idle, holding port until killed\n");
    for (;;) {
        pause();                            // 等 SIGTERM, 默认动作直接终止进程
    }

    return 0;                               // 不可达
}
