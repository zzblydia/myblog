#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <errno.h>
#include <netinet/in.h> // for sockaddr_in
#include <arpa/inet.h> // for inet_addr
#include <unistd.h> // for close

#define SERVER_ADDRESS "127.0.0.1"
#define SERVER_PORT 8080

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

    while (1) {
        printf("Listening...\n");

        if (listen(sock, 10) == -1) {
            perror("listen failed");
            close(sock);
            exit(EXIT_FAILURE);
        }

        int client_sock = accept(sock, NULL, NULL);
        if (client_sock == -1) {
            perror("accept failed");
            close(sock);
            exit(EXIT_FAILURE);
        } else {
            printf("\n");
            // get ip address of client
            struct sockaddr_in client_addr = {0};
            socklen_t addr_len = sizeof(client_addr);
            if (getpeername(client_sock, (struct sockaddr *) &client_addr, &addr_len) == -1) {
                perror("getpeername failed");
                close(client_sock);
                close(sock);
                exit(EXIT_FAILURE);
            }
            char client_ip[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, &client_addr.sin_addr, client_ip, sizeof(client_ip));
            printf("Accepted connection from client %s:%d\n", client_ip, ntohs(client_addr.sin_port));
        }

        char buffer[1024] = {0};
        int read_size = recv(client_sock, buffer, sizeof(buffer), 0);
        if (read_size == -1) {
            perror("recv failed");
            close(client_sock);
            close(sock);
            exit(EXIT_FAILURE);
        }

        printf("Received: %s\n", buffer);

        close(client_sock);
    }

    close(sock);
    return 0;
}