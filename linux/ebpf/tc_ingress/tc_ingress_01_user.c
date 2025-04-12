#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>

// Key for forwarding rules
struct rule_key {
    __u32 protocol;      // Protocol (IPPROTO_TCP or IPPROTO_UDP)
    __u32 src_ip;       // Source IP
    __u16 src_port;     // Source port
    __u32 dst_ip;       // Destination IP
    __u16 dst_port;     // Destination port
} __attribute__((packed));

// Value for forwarding rules
struct rule_value {
    __u32 rule_id;       // Rule ID (0-255)
    __u32 target_ip;    // Target IP
    __u16 target_port;  // Target port
} __attribute__((packed));

enum {
    LOG_LEVEL_OFF,
    LOG_LEVEL_CRITICAL,
    LOG_LEVEL_ERR,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_INFO,
    LOG_LEVEL_DEBUG,
} LOG_LEVEL;

int tc_ingress_user()
{
    // 还得是grok3, kimi不行
    int log_fd = bpf_obj_get("/sys/fs/bpf/tc/globals/log_switch_01"); // 假设 map 被 pin 在默认路径
    if (log_fd < 0) {
        printf("[%s:%d] Failed to open BPF map log_switch_01\n", __FUNCTION__, __LINE__);
        return 1;
    }

    __u32 log_key = 0;
    __u8 log_level = LOG_LEVEL_ERR; // Enable error
    if (bpf_map_update_elem(log_fd, &log_key, &log_level, BPF_ANY) < 0) {
        printf("[%s:%d] Failed to update log_enable_map\n", __FUNCTION__, __LINE__);
        return 1;
    }
    printf("Log level %u\n", log_level);

    int rules_fd = bpf_obj_get("/sys/fs/bpf/tc/globals/fwd_rules_01"); // 假设 map 被 pin 在默认路径
    if (rules_fd < 0) {
        printf("[%s:%d] Failed to open BPF map fwd_rules_01\n", __FUNCTION__, __LINE__);
        return 1;
    }

    // Set forward_rules (TCP: 192.168.23.52:8023 -> 192.168.23.62:8023 -> 192.168.23.62:18023)
    struct rule_key tcp_key = {
        .protocol = IPPROTO_TCP,
        .src_ip = inet_addr("192.168.23.52"),
        .src_port = htons(8023),
        .dst_ip = inet_addr("192.168.23.62"),
        .dst_port = htons(8023)
    };
    struct rule_value tcp_value = {
        .rule_id = 1,
        .target_ip = inet_addr("192.168.23.62"),
        .target_port = htons(18023)
    };
    if (bpf_map_update_elem(rules_fd, &tcp_key, &tcp_value, BPF_ANY) < 0) {
        perror("Failed to update forward_rules (TCP)");
        return 1;
    }
    printf("TCP rule added (rule_id=1)\n");

    // Set forward_rules (UDP: 192.168.23.52:8024 -> 192.168.23.62:8024 -> 192.168.23.62:18024)
    struct rule_key udp_key = {
        .protocol = IPPROTO_UDP,
        .src_ip = inet_addr("192.168.23.52"),
        .src_port = htons(8024),
        .dst_ip = inet_addr("192.168.23.62"),
        .dst_port = htons(8024)
    };
    struct rule_value udp_value = {
        .rule_id = 2,
        .target_ip = inet_addr("192.168.23.62"),
        .target_port = htons(18024)
    };
    if (bpf_map_update_elem(rules_fd, &udp_key, &udp_value, BPF_ANY) < 0) {
        perror("Failed to update forward_rules (UDP)");
        return 1;
    }
    printf("UDP rule added (rule_id=2)\n");

    return 0;
}

#ifdef _TC_INGRESS_01_MAIN
int main(int argc, char **argv)
{
    tc_ingress_user();
}
#endif