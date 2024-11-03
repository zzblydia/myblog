#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "ws-client-interface.h"

int MyCallback(unsigned short callbackIndex, int msgType) {
    printf("MyCallback: callbackIndex=%d, msgType=%d\n", callbackIndex, msgType);
    return 0;
}

char *g_serverAddress = "127.0.0.1";
unsigned short g_serverPort = 8080;

int main() {
    printf("Hello, World!\n");
    WstInit();
    WstClient client = {0};
    client.callbackIndex = 1;
    memcpy(client.serverAddress, g_serverAddress, strlen(g_serverAddress));
    client.serverPort = g_serverPort;
    client.eventCallback = MyCallback;

    WstConnect(&client);

    while (1) {
        WstPoll(&client);
        usleep(100);
    }
    return 0;
}