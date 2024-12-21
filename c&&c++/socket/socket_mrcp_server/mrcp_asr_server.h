#ifndef MRCP_ASR_SERVER_H
#define MRCP_ASR_SERVER_H

#define BUFFER_SIZE 1024

void get_timestamp(char *timestamp);

void request_and_response(int client_sock, char *recv, int read_size);

#endif
