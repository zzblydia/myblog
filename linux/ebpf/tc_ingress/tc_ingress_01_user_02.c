#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <linux/bpf.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include <net/if.h>

// libbpf 日志回调函数
static int libbpf_print_fn(enum libbpf_print_level level, const char *format, va_list args) {
    return vfprintf(stderr, format, args);
}

struct rule_key {
    __u8 protocol;
    __u32 src_ip;
    __u16 src_port;
    __u32 dst_ip;
    __u16 dst_port;
};

struct rule_value {
    __u8 rule_id;
    __u32 target_ip;
    __u16 target_port;
};

int main(int argc, char **argv) {
    struct bpf_object *obj = NULL;
    struct bpf_program *prog = NULL;
    struct bpf_map *log_map = NULL, *rules_map = NULL;
    struct bpf_tc_hook tc_hook = {0};
    struct bpf_tc_opts tc_opts = {0};
    int log_fd = -1, rules_fd = -1;
    int ifindex;
    int ret;

    // 0. 检查参数
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <interface>\n", argv[0]);
        fprintf(stderr, "Example: %s eth0\n", argv[0]);
        return 1;
    }

    // 获取网络接口索引
    ifindex = if_nametoindex(argv[1]);
    if (ifindex == 0) {
        fprintf(stderr, "Failed to get interface index for %s: %s\n", argv[1], strerror(errno));
        return 1;
    }

    // 1. 启用 libbpf 日志
    libbpf_set_print(libbpf_print_fn);

    // 2. 打开 eBPF 程序
    obj = bpf_object__open_file("ebpf_tc_ingress_01_kernel.o", NULL);
    if (libbpf_get_error(obj)) {
        fprintf(stderr, "Failed to open eBPF object file: %s\n", strerror(errno));
        return 1;
    }

    // 3. 加载 eBPF 程序
    ret = bpf_object__load(obj);
    if (ret) {
        fprintf(stderr, "Failed to load eBPF object: %s\n", strerror(errno));
        bpf_object__close(obj);
        return 1;
    }

    // 4. 查找 eBPF 程序
    prog = bpf_object__find_program_by_name(obj, "tc_ingress_01_kernel");
    if (!prog) {
        fprintf(stderr, "Failed to find tc_ingress_01_kernel program\n");
        bpf_object__close(obj);
        return 1;
    }

    // 5. 设置 TC 钩子并附加程序
    tc_hook.sz = sizeof(tc_hook);
    tc_hook.ifindex = ifindex;
    tc_hook.attach_point = BPF_TC_INGRESS;

    // 创建 TC 钩子（如果不存在）
    ret = bpf_tc_hook_create(&tc_hook);
    if (ret && ret != -EEXIST) {
        fprintf(stderr, "Failed to create TC hook: %s\n", strerror(-ret));
        bpf_object__close(obj);
        return 1;
    }

    // 附加 TC 程序
    tc_opts.sz = sizeof(tc_opts);
    tc_opts.prog_fd = bpf_program__fd(prog);
    ret = bpf_tc_attach(&tc_hook, &tc_opts);
    if (ret) {
        fprintf(stderr, "Failed to attach TC program: %s\n", strerror(-ret));
        bpf_tc_hook_destroy(&tc_hook);
        bpf_object__close(obj);
        return 1;
    }

    // 6. 查找 log_enable_map
    log_map = bpf_object__find_map_by_name(obj, "log_enable_map");
    if (!log_map) {
        fprintf(stderr, "Failed to find log_enable_map\n");
        goto cleanup;
    }

    log_fd = bpf_map__fd(log_map);
    if (log_fd < 0) {
        fprintf(stderr, "Failed to get log_enable_map fd: %s\n", strerror(errno));
        goto cleanup;
    }

    // 7. Pin log_enable_map 以持久化
    ret = bpf_obj_pin(log_fd, "/sys/fs/bpf/log_enable_map");
    if (ret) {
        fprintf(stderr, "Failed to pin log_enable_map: %s\n", strerror(errno));
        goto cleanup;
    }
    printf("Pinned log_enable_map to /sys/fs/bpf/log_enable_map\n");

    // 8. 更新 log_enable_map
    __u32 log_key = 0;
    __u8 log_value = 1; // Enable logging
    ret = bpf_map_update_elem(log_fd, &log_key, &log_value, BPF_ANY);
    if (ret) {
        fprintf(stderr, "Failed to update log_enable_map: %s\n", strerror(errno));
        goto cleanup;
    }
    printf("Log enabled (log_enable_map[0] = %u)\n", log_value);

    // 9. 查找 forward_rules map
    rules_map = bpf_object__find_map_by_name(obj, "forward_rules");
    if (!rules_map) {
        fprintf(stderr, "Failed to find forward_rules map\n");
        goto cleanup;
    }

    rules_fd = bpf_map__fd(rules_map);
    if (rules_fd < 0) {
        fprintf(stderr, "Failed to get forward_rules fd: %s\n", strerror(errno));
        goto cleanup;
    }

    // 10. Pin forward_rules 以持久化
    ret = bpf_obj_pin(rules_fd, "/sys/fs/bpf/forward_rules");
    if (ret) {
        fprintf(stderr, "Failed to pin forward_rules: %s\n", strerror(errno));
        goto cleanup;
    }
    printf("Pinned forward_rules to /sys/fs/bpf/forward_rules\n");

    // 11. 设置 TCP 转发规则
    struct rule_key tcp_key = {
        .protocol = IPPROTO_TCP,
        .src_ip = inet_addr("192.168.23.1"),
        .src_port = htons(8023),
        .dst_ip = inet_addr("192.168.23.62"),
        .dst_port = htons(8023)
    };
    struct rule_value tcp_value = {
        .rule_id = 1,
        .target_ip = inet_addr("192.168.23.62"),
        .target_port = htons(18023)
    };
    ret = bpf_map_update_elem(rules_fd, &tcp_key, &tcp_value, BPF_ANY);
    if (ret) {
        fprintf(stderr, "Failed to update forward_rules (TCP): %s\n", strerror(errno));
        goto cleanup;
    }
    printf("TCP rule added (rule_id=1)\n");

    // 12. 设置 UDP 转发规则
    struct rule_key udp_key = {
        .protocol = IPPROTO_UDP,
        .src_ip = inet_addr("192.168.23.1"),
        .src_port = htons(8024),
        .dst_ip = inet_addr("192.168.23.62"),
        .dst_port = htons(8024)
    };
    struct rule_value udp_value = {
        .rule_id = 2,
        .target_ip = inet_addr("192.168.23.62"),
        .target_port = htons(18024)
    };
    ret = bpf_map_update_elem(rules_fd, &udp_key, &udp_value, BPF_ANY);
    if (ret) {
        fprintf(stderr, "Failed to update forward_rules (UDP): %s\n", strerror(errno));
        goto cleanup;
    }
    printf("UDP rule added (rule_id=2)\n");

    // 13. Pin 程序以持久化（可选）
    ret = bpf_obj_pin(bpf_program__fd(prog), "/sys/fs/bpf/tc_ingress");
    if (ret) {
        fprintf(stderr, "Failed to pin tc_ingress program: %s\n", strerror(errno));
        goto cleanup;
    }
    printf("Pinned tc_ingress program to /sys/fs/bpf/tc_ingress\n");

    printf("eBPF program and maps configured successfully. Persisted to /sys/fs/bpf/\n");

cleanup:
    // 关闭 fd，但 pinned 的对象和附加的程序会继续存在
    if (log_fd >= 0)
        close(log_fd);
    if (rules_fd >= 0)
        close(rules_fd);
    if (obj)
        bpf_object__close(obj);
    // 注意：不销毁 tc_hook 和 tc_opts，让程序保持附加
    return ret ? 1 : 0;
}