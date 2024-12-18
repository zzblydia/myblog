#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <errno.h>
#include <netinet/in.h> // for sockaddr_in
#include <arpa/inet.h> // for inet_addr
#include <unistd.h> // for close
#include <string.h>
#include <pthread.h> // for pthread
#include "mrcp_asr_server.h"

#define SERVER_ADDRESS "127.0.0.1"
#define SERVER_PORT 8080
#define BUFFER_SIZE 1024

void print_client_info(int client_sock) {
    // get ip and port of client
    struct sockaddr_in client_addr = {0};
    socklen_t addr_len = sizeof(client_addr);
    if (getpeername(client_sock, (struct sockaddr *) &client_addr, &addr_len) == -1) {
        perror("getpeername failed");
        close(client_sock);
        exit(EXIT_FAILURE);
    }
    char client_ip[INET_ADDRSTRLEN] = {0};
    inet_ntop(AF_INET, &client_addr.sin_addr, client_ip, sizeof(client_ip));

    // get timestamp with seconds and microseconds
    char timestamp[64] = {0};
    get_timestamp(timestamp);

    printf("[%s] connect from %s:%d with fd %d\n", timestamp, client_ip, ntohs(client_addr.sin_port), client_sock);
}

// 客户端处理函数
void *handle_client(void *client_sock_ptr) {
    int client_sock = *(int *) client_sock_ptr; // 将指针转换为整型
    free(client_sock_ptr); // 释放动态分配的内存

    int read_size;
    while (1) {
        char buffer[BUFFER_SIZE] = {0};
        read_size = recv(client_sock, buffer, sizeof(buffer), 0);
        if (read_size == 0) {
            break; // 客户端断开连接
        } else if (read_size == -1) {
            perror("recv failed");
            break;
        }

        char response[BUFFER_SIZE] = {0};
        int len = request_and_response(client_sock, buffer, read_size, response);
        send(client_sock, response, len, 0);

        // 清空缓冲区
        memset(buffer, 0, sizeof(buffer));
    }

    // 关闭客户端Socket
    close(client_sock);
    return NULL;
}

int main() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == -1) {
        printf("socket create failed errno %d\n", errno);
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in server_addr = {0};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    server_addr.sin_addr.s_addr = inet_addr(SERVER_ADDRESS);
    if (bind(sock, (struct sockaddr *) &server_addr, sizeof(server_addr)) == -1) {
        perror("bind failed");
        close(sock);
        exit(EXIT_FAILURE);
    }

    if (listen(sock, 10) == -1) {
        perror("listen failed");
        close(sock);
        exit(EXIT_FAILURE);
    }

    printf("Server is listening on %s:%d\n", SERVER_ADDRESS, SERVER_PORT);

    while (1) {
        // 接受连接
        int *client_sock = malloc(sizeof(int)); // 动态分配内存以传递给线程
        *client_sock = accept(sock, NULL, NULL);
        if (*client_sock == -1) {
            perror("accept failed");
            free(client_sock); // 释放内存
            continue; // 继续等待下一个客户端
        }

        print_client_info(*client_sock);

        // 创建新线程处理客户端
        pthread_t tid;
        if (pthread_create(&tid, NULL, handle_client, client_sock) != 0) {
            perror("pthread_create failed");
            close(*client_sock); // 关闭套接字
            free(client_sock); // 释放内存
            continue; // 继续等待下一个客户端
        }

        // Detach the thread so that its resources are released when it terminates
        pthread_detach(tid);
    }

    close(sock);
    return 0;
}