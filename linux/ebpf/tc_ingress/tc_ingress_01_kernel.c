#include <linux/bpf.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/in.h>
#include <bpf/bpf_helpers.h>

#include <bpf/bpf_endian.h> // for bpf_ntohs

// Port range for destination port check
#define PORT_MIN 8023
#define PORT_MAX 8024

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

// Hash map to store forwarding rules
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 256);
    __type(key, struct rule_key);
    __type(value, struct rule_value);
    __uint(pinning, LIBBPF_PIN_BY_NAME);  // 添加 pinning 属性
} fwd_rules_01 SEC(".maps");

// Global array to store logging configuration
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u8);
    __uint(pinning, LIBBPF_PIN_BY_NAME);  // 添加 pinning 属性
} log_switch_01 SEC(".maps");

// Validate packet headers
static __always_inline int packets_valid_check(struct __sk_buff *skb, struct ethhdr **eth, struct iphdr **ip)
{
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    // Parse Ethernet header
    *eth = data;
    if ((void *)(*eth + 1) > data_end)
        return 0;

    // Check if packet is IP
    if ((*eth)->h_proto != __constant_htons(ETH_P_IP))
        return 0;

    // Parse IP header
    *ip = (void *)(*eth + 1);
    if ((void *)(*ip + 1) > data_end)
        return 0;

    // Check if protocol is TCP or UDP
    if ((*ip)->protocol != IPPROTO_TCP && (*ip)->protocol != IPPROTO_UDP)
        return 0;

    return 1;
}

// Update IP checksum
static __always_inline void update_ip_checksum(struct iphdr *ip)
{
    __u32 csum = 0;
    __u16 *ptr = (__u16 *)ip;
    int len = sizeof(*ip) / 2;

    ip->check = 0;
    for (int i = 0; i < len; i++)
        csum += ptr[i];
    csum = (csum & 0xFFFF) + (csum >> 16);
    csum = (csum & 0xFFFF) + (csum >> 16);
    ip->check = ~csum;
}

// Update TCP/UDP checksum
static __always_inline void update_l4_checksum(struct __sk_buff *skb, struct iphdr *ip, void *l4_hdr, __u8 protocol,
    __u32 old_ip, __u16 old_port)
{
    void *data_end = (void *)(long)skb->data_end;
    __u32 csum;

    // Get existing checksum and new values
    __u32 new_ip = ip->daddr;
    __u16 new_port;
    if (protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = l4_hdr;
        if ((void *)(tcp + 1) > data_end)
            return;
        csum = ~bpf_ntohs(tcp->check); // Invert to original sum
        new_port = tcp->dest;
        tcp->check = 0;
    } else { // UDP
        struct udphdr *udp = l4_hdr;
        if ((void *)(udp + 1) > data_end)
            return;
        csum = (udp->check == 0) ? 0 : ~bpf_ntohs(udp->check); // Handle optional UDP checksum
        new_port = udp->dest;
        udp->check = 0;
    }

    // Incremental update: subtract old values, add new values
    csum -= old_ip & 0xFFFF;
    csum -= (old_ip >> 16) & 0xFFFF;
    csum -= old_port;
    csum += new_ip & 0xFFFF;
    csum += (new_ip >> 16) & 0xFFFF;
    csum += new_port;

    // Fold checksum
    csum = (csum & 0xFFFF) + (csum >> 16);
    csum = (csum & 0xFFFF) + (csum >> 16);

    // Set checksum
    __u16 final_csum = ~csum;
    if (protocol == IPPROTO_TCP) {
        ((struct tcphdr *)l4_hdr)->check = bpf_htons(final_csum);
    } else { // UDP
        ((struct udphdr *)l4_hdr)->check = (final_csum == 0) ? bpf_htons(0xFFFF) : bpf_htons(final_csum);
    }
}

// Process TCP packet
static __always_inline int process_tcp_packet(struct __sk_buff *skb, struct iphdr *ip)
{
    void *data_end = (void *)(long)skb->data_end;
    struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
    if ((void *)(tcp + 1) > data_end)
        return TC_ACT_OK;

    // Ignore packets with destination port outside PORT_MIN-PORT_MAX
    if (bpf_ntohs(tcp->dest) < PORT_MIN || bpf_ntohs(tcp->dest) > PORT_MAX)
        return TC_ACT_OK;


    // Initialize rule key
    struct rule_key key = {
        .protocol = ip->protocol,
        .src_ip = ip->saddr,
        .src_port = tcp->source,
        .dst_ip = ip->daddr,
        .dst_port = tcp->dest,
    };

    // Lookup forwarding rule
    __u8 log_enable = 1;
    __u32 log_key = 0;
    __u8 *log_ptr = bpf_map_lookup_elem(&log_switch_01, &log_key);
    if (log_ptr) {
        log_enable = *log_ptr;
        bpf_printk("process_tcp_packet: log_ptr not null log_enable %u, sizeof(rule_key) %u, sizeof(rule_value) %u\n", log_enable,
            sizeof(struct rule_key), sizeof(struct rule_value));
    } else {
        bpf_printk("process_tcp_packet: log_ptr null\n");
    }

    if (log_enable) {
        bpf_printk("process_tcp_packet: protocol=%u, src=%u:%u, dst=%u:%u\n", ip->protocol, ip->saddr, tcp->source, ip->daddr, tcp->dest);
    }

    struct rule_value *value = bpf_map_lookup_elem(&fwd_rules_01, &key);
    if (value) {
        if (log_enable) {
            bpf_printk("process_tcp_packet: protocol=%u, src=%u:%u, dst=%u:%u, rule_id=%u, target=%x:%u\n", key.protocol, bpf_ntohl(key.src_ip), bpf_ntohs(key.src_port),
                bpf_ntohl(key.dst_ip), bpf_ntohs(key.dst_port), value->rule_id, bpf_ntohl(value->target_ip), bpf_ntohs(value->target_port));
        }

        // Store old values for checksum update
        __u32 old_ip = ip->daddr;
        __u16 old_port = tcp->dest;

        // Modify destination IP and port
        ip->daddr = value->target_ip;
        tcp->dest = value->target_port;

        // Update checksums
        update_ip_checksum(ip);
        update_l4_checksum(skb, ip, tcp, IPPROTO_TCP, old_ip, old_port);
    } else {
        bpf_printk("process_tcp_packet failed src=%x:%u\n", bpf_ntohl(key.src_ip), bpf_ntohs(key.src_port));
    }

    return TC_ACT_OK;
}

// Process UDP packet
static __always_inline int process_udp_packet(struct __sk_buff *skb, struct iphdr *ip)
{

    void *data_end = (void *)(long)skb->data_end;
    struct udphdr *udp = (void *)ip + (ip->ihl * 4);
    if ((void *)(udp + 1) > data_end)
        return TC_ACT_OK;
    
        // Ignore packets with destination port outside PORT_MIN-PORT_MAX
    if (bpf_ntohs(udp->dest) < PORT_MIN || bpf_ntohs(udp->dest) > PORT_MAX)
        return TC_ACT_OK;
    
    // Initialize rule key
    struct rule_key key = {
        .protocol = ip->protocol,
        .src_ip = ip->saddr,
        .src_port = udp->source,
        .dst_ip = ip->daddr,
        .dst_port = udp->dest,
    };

    // Lookup forwarding rule
    __u8 log_enable = 1;
    struct rule_value *value = bpf_map_lookup_elem(&fwd_rules_01, &key);
    if (value) {
        // Read log enable flag from global array
        __u32 log_key = 0;
        __u8 *log_val = bpf_map_lookup_elem(&log_switch_01, &log_key);
        if (log_val)
            log_enable = *log_val;

        if (log_enable) {
            // bpf_trace_printk参数只能有3个. cat /sys/kernel/debug/tracing/trace_pipe
            // bpf_printk dmesg
            bpf_printk("process_udp_packet: rule_id=%u, src=%x:%u\n", value->rule_id, bpf_ntohl(key.src_ip), bpf_ntohs(key.src_port));
            bpf_printk("process_udp_packet: rule_id=%u, dst=%x:%u\n", value->rule_id, bpf_ntohl(key.dst_ip), bpf_ntohs(key.dst_port));
            bpf_printk("process_udp_packet: rule_id=%u, target=%x:%u\n", value->rule_id, bpf_ntohl(value->target_ip), bpf_ntohs(value->target_port));
        }

        // Store old values for checksum update
        __u32 old_ip = ip->daddr;
        __u16 old_port = udp->dest;

        // Modify destination IP and port
        ip->daddr = value->target_ip;
        udp->dest = value->target_port;

        // Update checksums
        update_ip_checksum(ip);
        update_l4_checksum(skb, ip, udp, IPPROTO_UDP, old_ip, old_port);
    } else {
        bpf_printk("process_udp_packet failed src=%x:%u\n", bpf_ntohl(key.src_ip), bpf_ntohs(key.src_port));
    }

    return TC_ACT_OK;
}

SEC("classifier")
int tc_ingress_01(struct __sk_buff *skb)
{
    struct ethhdr *eth;
    struct iphdr *ip;

    // Validate packet
    if (!packets_valid_check(skb, &eth, &ip))
        return TC_ACT_OK;

    // Process TCP or UDP packet
    if (ip->protocol == IPPROTO_TCP)
        return process_tcp_packet(skb, ip);
    else if (ip->protocol == IPPROTO_UDP)
        return process_udp_packet(skb, ip);

    return TC_ACT_OK;
}

char _license[] SEC("license") = "GPL";
