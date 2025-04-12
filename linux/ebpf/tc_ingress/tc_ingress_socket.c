#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <pthread.h>

#define SERVER_IP "192.168.23.62"
#define TCP_PORT 18023
#define UDP_PORT 18024
#define BUFFER_SIZE 1024

// 打印数据包信息
void print_packet_info(const struct sockaddr_in *src_addr, const struct sockaddr_in *dst_addr, int length) {
    char src_ip_str[INET_ADDRSTRLEN] = {0};
    char dst_ip_str[INET_ADDRSTRLEN] = {0};
    inet_ntop(AF_INET, &src_addr->sin_addr, src_ip_str, INET_ADDRSTRLEN);
    inet_ntop(AF_INET, &dst_addr->sin_addr, dst_ip_str, INET_ADDRSTRLEN);

    printf("Src IP: %s, Src Port: %d, Dst IP: %s, Dst Port: %d, Length: %d\n",
           src_ip_str, ntohs(src_addr->sin_port), dst_ip_str, ntohs(dst_addr->sin_port), length);
}

// TCP 监听函数
void tcp_listen() {
    int tcp_socket;
    struct sockaddr_in tcp_server_addr, tcp_client_addr;
    socklen_t tcp_client_len = sizeof(tcp_client_addr);

    // 创建 TCP 套接字
    tcp_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (tcp_socket < 0) {
        perror("TCP socket creation failed");
        exit(EXIT_FAILURE);
    }

    // 配置服务器地址
    memset(&tcp_server_addr, 0, sizeof(tcp_server_addr));
    tcp_server_addr.sin_family = AF_INET;
    tcp_server_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
    tcp_server_addr.sin_port = htons(TCP_PORT);

    // 绑定套接字
    if (bind(tcp_socket, (struct sockaddr *)&tcp_server_addr, sizeof(tcp_server_addr)) < 0) {
        perror("TCP bind failed");
        close(tcp_socket);
        exit(EXIT_FAILURE);
    }

    // 监听连接
    if (listen(tcp_socket, 10) < 0) {
        perror("TCP listen failed");
        close(tcp_socket);
        exit(EXIT_FAILURE);
    }

    printf("TCP server listening on port %d\n", TCP_PORT);

    while (1) {
        int client_socket = accept(tcp_socket, (struct sockaddr *)&tcp_client_addr, &tcp_client_len);
        if (client_socket < 0) {
            perror("TCP accept failed");
            continue;
        }

        char buffer[BUFFER_SIZE];
        int length = read(client_socket, buffer, BUFFER_SIZE);
        if (length < 0) {
            perror("TCP read failed");
            close(client_socket);
            continue;
        }

        // 打印数据包信息
        print_packet_info(&tcp_client_addr, &tcp_server_addr, length);

        close(client_socket);
    }

    close(tcp_socket);
}

// UDP 监听函数
void udp_listen() {
    int udp_socket;
    struct sockaddr_in udp_server_addr, udp_client_addr;
    socklen_t udp_client_len = sizeof(udp_client_addr);

    // 创建 UDP 套接字
    udp_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (udp_socket < 0) {
        perror("UDP socket creation failed");
        exit(EXIT_FAILURE);
    }

    // 配置服务器地址
    memset(&udp_server_addr, 0, sizeof(udp_server_addr));
    udp_server_addr.sin_family = AF_INET;
    udp_server_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
    udp_server_addr.sin_port = htons(UDP_PORT);

    // 绑定套接字
    if (bind(udp_socket, (struct sockaddr *)&udp_server_addr, sizeof(udp_server_addr)) < 0) {
        perror("UDP bind failed");
        close(udp_socket);
        exit(EXIT_FAILURE);
    }

    printf("UDP server listening on port %d\n", UDP_PORT);

    while (1) {
        char buffer[BUFFER_SIZE];
        int length = recvfrom(udp_socket, buffer, BUFFER_SIZE, 0, (struct sockaddr *)&udp_client_addr, &udp_client_len);
        if (length < 0) {
            perror("UDP recvfrom failed");
            continue;
        }

        // 打印数据包信息
        print_packet_info(&udp_client_addr, &udp_server_addr, length);
    }

    close(udp_socket);
}


int main() {
    pthread_t tcp_thread, udp_thread;

    // 创建线程分别监听 TCP 和 UDP
    if (pthread_create(&tcp_thread, NULL, (void *(*)(void *))tcp_listen, NULL) != 0) {
        perror("Failed to create TCP thread");
        exit(EXIT_FAILURE);
    }

    if (pthread_create(&udp_thread, NULL, (void *(*)(void *))udp_listen, NULL) != 0) {
        perror("Failed to create UDP thread");
        exit(EXIT_FAILURE);
    }
    
    tc_ingress_user();

    // 等待线程结束
    pthread_join(tcp_thread, NULL);
    pthread_join(udp_thread, NULL);

    return 0;
}
