#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <errno.h>
#include <netinet/in.h> // for sockaddr_in
#include <arpa/inet.h> // for inet_addr
#include <unistd.h> // for close

#define SERVER_ADDRESS "127.0.0.1"
#define SERVER_PORT 8080
#define CLIENT_ADDRESS "127.0.0.1"
#define CLIENT_PORT 12345

int main() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == -1) {
        printf("socket create failed errno %d\n", errno);
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in client_addr = {0};
    client_addr.sin_family = AF_INET;
    client_addr.sin_port = htons(CLIENT_PORT);  //
    client_addr.sin_addr.s_addr = inet_addr(CLIENT_ADDRESS);
    if (bind(sock, (struct sockaddr *) &client_addr, sizeof(client_addr)) == -1) {
        perror("bind failed");
        close(sock);
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in server_addr = {0};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    server_addr.sin_addr.s_addr = inet_addr(SERVER_ADDRESS);
    if (connect(sock, (struct sockaddr *) &server_addr, sizeof(server_addr)) == -1) {
        perror("connect failed");
        close(sock);
        exit(EXIT_FAILURE);
    }

    char buffer[1024] = "hello from client";
    if (send(sock, buffer, sizeof(buffer), 0) == -1) {
        perror("send failed");
        close(sock);
        exit(EXIT_FAILURE);
    }

    close(sock);
    return 0;
}