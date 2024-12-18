#include <stdio.h>
// #include <pthread.h> // 如果不引入这个, 就要引入#include<time.h> 否则strftime报错
#include <time.h> // for strftime
#include <sys/time.h> // for gettimeofday

#include "mrcp_asr_server.h"

void get_timestamp(char *timestamp) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    strftime(timestamp, 64, "%Y%m%d-%H-%M-%S", localtime(&tv.tv_sec));
    sprintf(timestamp, "%s-%ld", timestamp, tv.tv_usec);
}

int request_and_response(int client_sock, char *buffer, int read_size, char* sendbuf) {
    char timestamp[64] = {0};
    get_timestamp(timestamp);

    buffer[read_size] = '\0'; // 确保字符串以 NULL 结尾
    printf("[%s] recv [%s]", timestamp, buffer);
    return 0;
}
