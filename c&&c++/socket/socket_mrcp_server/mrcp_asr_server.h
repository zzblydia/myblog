#ifndef MRCP_ASR_SERVER_H
#define MRCP_ASR_SERVER_H

void get_timestamp(char *timestamp);

int request_and_response(int client_sock, char *recv, int read_size, char* sendbuf);

#endif
