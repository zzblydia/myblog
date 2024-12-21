#include <stdio.h>
#include <string.h>
// #include <pthread.h> // 如果不引入这个, 就要引入#include<time.h> 否则strftime报错
#include <time.h> // for strftime
#include <sys/time.h> // for gettimeofday
#include <sys/socket.h>
#include <unistd.h>

#include "mrcp_asr_server.h"

char *resp_define_grammar = "MRCP/2.0 %d %d 200 COMPLETE\r\nChannel-Identifier: %s\r\nCompletion-Cause: 000 success\r\n\r\n";
char *resp_recognize = "MRCP/2.0 %d %d 200 IN-PROGRESS\r\nChannel-Identifier: %s\r\n\r\n";
char* start_of_input = "MRCP/2.0 %d START-OF-INPUT %d IN-PROGRESS\r\nChannel-Identifier: %s\r\n\r\n";
char* intermediate_result = "MRCP/2.0 %d INTERMEDIATE-RESULT %d IN-PROGRESS\r\nChannel-Identifier: %s\r\nCompletion-Cause: 000 success\r\nContent-Type: application/nlsml+xml\r\nContent-Length: 266\r\n\r\n<?xml version=\"1.0\" encoding=\"UTF-8\"><result grammar=\"session:<14101459@7.202.2.95>\"><interpretation confidence=\"0.99\" grammar=\"session:<14101459@7.202.2.95>\"><instance>12345</instance><input mode=\"speech-to-text\">abcdef</input></interpretation></result>";
char *resp_stop = "MRCP/2.0 %d %d 200 COMPLETE\r\nChannel-Identifier: %s\r\nActive-Request-Id-List: 2\r\n\r\n";

// 以下几个函数会被多线程调用, 不要使用全局变量

void get_timestamp(char *timestamp) 
{
    struct timeval tv;
    gettimeofday(&tv, NULL);
    strftime(timestamp, 64, "%Y%m%d-%H-%M-%S", localtime(&tv.tv_sec));
    sprintf(timestamp, "%s-%ld", timestamp, tv.tv_usec);
}

void handle_define_grammar(int client_sock, char *buffer, int read_size)
{
    char *line = strtok(buffer, "\r\n");  // 分割每一行
    int transNum = 0;
    if (line != NULL) {
        sscanf(line, "MRCP/2.0 %*d DEFINE-GRAMMAR %d", &transNum); 
        // printf("[%s:%d] transNum %d \n", __FUNCTION__, __LINE__, transNum);
    }
    line = strtok(NULL, "\r\n"); // 处理第二行
    if (line == NULL) {
        printf("[%s:%d]parse Channel-Identifier error %s\n", __FUNCTION__, __LINE__, buffer);
        return;
    }

    char channel_id[100] = {0};
    char timestamp[64] = {0};
    char strLenLen[10] = {0}; // 长度的长度
    int lenLen;
    if (strstr(line, "Channel-Identifier:") != NULL) {
        sscanf(line + strlen("Channel-Identifier: "), "%s", channel_id);

        int len = (strlen(resp_define_grammar) - 2 - 2)+ (strlen(channel_id) - 2);
        memset(strLenLen, 0 , 10);
        lenLen = sprintf(strLenLen, "%d", len);
        len += lenLen;
        memset(strLenLen, 0 , 10);
        lenLen = sprintf(strLenLen, "%d", transNum);
        len += lenLen;

        // 发送响应
        char response[BUFFER_SIZE] = {0};
        int length =  sprintf(response, resp_define_grammar, len, transNum, channel_id);
        send(client_sock, response, length, 0);
        get_timestamp(timestamp);
        printf("[%s] fd %d response [%s]\n", timestamp, client_sock, response);
    }
}

void handle_recognize(int client_sock, char *buffer, int read_size)
{
    char *line = strtok(buffer, "\r\n");  // 分割每一行
    int transNum = 0;
    if (line != NULL) {
        sscanf(line, "MRCP/2.0 %*d RECOGNIZE %d", &transNum);
        // printf("[%s:%d] transNum %d \n", __FUNCTION__, __LINE__, transNum);
    }
    line = strtok(NULL, "\r\n"); // 处理第二行
    if (line == NULL) {
        printf("[%s:%d]parse Channel-Identifier error %s\n", __FUNCTION__, __LINE__, buffer);
        return;
    }
    char channel_id[100] = {0};
    char strLenLen[10] = {0}; // 长度的长度
    char response[BUFFER_SIZE] = {0};
    char timestamp[64] = {0};
    int lenLen;
    if (strstr(line, "Channel-Identifier:") != NULL) {
        sscanf(line + strlen("Channel-Identifier: "), "%s", channel_id);

        // 200
        int len = (strlen(resp_recognize) - 2 - 2)+ (strlen(channel_id) - 2);
        memset(strLenLen, 0 , 10);
        lenLen = sprintf(strLenLen, "%d", len);
        len += lenLen;
        memset(strLenLen, 0 , 10);
        lenLen = sprintf(strLenLen, "%d", transNum);
        len += lenLen;

        // 发送响应
        memset(response, 0 , BUFFER_SIZE);
        int length =  sprintf(response, resp_recognize, len, transNum, channel_id);
        send(client_sock, response, length, 0);
        get_timestamp(timestamp);
        printf("[%s] fd %d response [%s]\n", timestamp, client_sock, response);

        // START_OF_INPUT
        sleep(1);
        len = (strlen(start_of_input) - 2 - 2)+ (strlen(channel_id) - 2);
        memset(strLenLen, 0 , 10);
        lenLen = sprintf(strLenLen, "%d", len);
        len += lenLen;
        memset(strLenLen, 0 , 10);
        lenLen = sprintf(strLenLen, "%d", transNum);
        len += lenLen;
        // 发送响应
        memset(response, 0 , BUFFER_SIZE);
        length =  sprintf(response, start_of_input, len, transNum, channel_id);
        send(client_sock, response, length, 0);
        get_timestamp(timestamp);
        printf("[%s] fd %d response [%s]\n", timestamp, client_sock, response);

        // INTERMEDIATE-RESULT
        sleep(1);
        len = (strlen(intermediate_result) - 2 - 2)+ (strlen(channel_id) - 2);
        memset(strLenLen, 0 , 10);
        lenLen = sprintf(strLenLen, "%d", len);
        len += lenLen;
        memset(strLenLen, 0 , 10);
        lenLen = sprintf(strLenLen, "%d", transNum);
        len += lenLen;

        // 发送响应
        memset(response, 0 , BUFFER_SIZE);
        length =  sprintf(response, intermediate_result, len, transNum, channel_id);
        send(client_sock, response, length, 0);
        get_timestamp(timestamp);
        printf("[%s] fd %d response [%s]\n", timestamp, client_sock, response);

        // INTERMEDIATE-RESULT
        sleep(1);
        send(client_sock, response, length, 0);
        get_timestamp(timestamp);
        printf("[%s] fd %d response [%s]\n", timestamp, client_sock, response);

        // INTERMEDIATE-RESULT
        sleep(1);
        send(client_sock, response, length, 0);
        get_timestamp(timestamp);
        printf("[%s] fd %d response [%s]\n", timestamp, client_sock, response);

        // INTERMEDIATE-RESULT
        sleep(1);
        send(client_sock, response, length, 0);
        get_timestamp(timestamp);
        printf("[%s] fd %d response [%s]\n", timestamp, client_sock, response);

        // INTERMEDIATE-RESULT
        sleep(1);
        send(client_sock, response, length, 0);
        get_timestamp(timestamp);
        printf("[%s] fd %d response [%s]\n", timestamp, client_sock, response);
    }
}

void handle_stop(int client_sock, char *buffer, int read_size)
{
    char *line = strtok(buffer, "\r\n");  // 分割每一行
    int transNum = 0;
    if (line != NULL) {
        sscanf(line, "MRCP/2.0 %*d STOP %d", &transNum);
        // printf("[%s:%d] transNum %d \n", __FUNCTION__, __LINE__, transNum);
    }
    line = strtok(NULL, "\r\n"); // 处理第二行
    if (line == NULL) {
        printf("[%s:%d]parse Channel-Identifier error %s\n", __FUNCTION__, __LINE__, buffer);
        return;
    }

    char channel_id[100] = {0};
    char timestamp[64] = {0};
    char strLenLen[10] = {0}; // 长度的长度
    int lenLen;
    if (strstr(line, "Channel-Identifier:") != NULL) {
        sscanf(line + strlen("Channel-Identifier: "), "%s", channel_id);
        int len = (strlen(resp_stop) - 2 - 2)+ (strlen(channel_id) - 2);
        memset(strLenLen, 0 , 10);
        lenLen = sprintf(strLenLen, "%d", len);
        len += lenLen;
        memset(strLenLen, 0 , 10);
        lenLen = sprintf(strLenLen, "%d", transNum);
        len += lenLen;

        // 发送响应
        char response[BUFFER_SIZE] = {0};
        int length =  sprintf(response, resp_stop, len, transNum, channel_id);
        send(client_sock, response, len, 0);
        get_timestamp(timestamp);
        printf("[%s] fd %d response [%s]\n", timestamp, client_sock, response);
    }
}

void request_and_response(int client_sock, char *buffer, int read_size)
 {
    char timestamp[64] = {0};
    get_timestamp(timestamp);

    buffer[read_size] = '\0'; // 确保字符串以 NULL 结尾
    printf("[%s] fd %d recv [%s]\n", timestamp, client_sock, buffer);

    // handle mrcp request
    if (strstr(buffer, "DEFINE-GRAMMAR") != 0) {
        handle_define_grammar(client_sock, buffer, read_size);
    } else if (strstr(buffer, "RECOGNIZE") != 0) {
        handle_recognize(client_sock, buffer, read_size);
    } else if (strstr(buffer, "STOP") != 0) {
        handle_stop(client_sock, buffer, read_size);
    }
}
