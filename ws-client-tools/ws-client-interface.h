#ifndef WS_CLIENT_INTERFACE_H
#define WS_CLIENT_INTERFACE_H

typedef int (*EventCallback)(unsigned short callbackIndex, int msgType);

#define WS_GENERAL_LEN 128
typedef struct {
    unsigned short callbackIndex;

    char clientIp[WS_GENERAL_LEN];
    unsigned short clientPort;
    int ssl;    // 0 for no ssl, 1 for ssl with pem cert, 2 for ssl with ca cert
    char certPath[WS_GENERAL_LEN];

    char serverAddress[WS_GENERAL_LEN];
    unsigned short serverPort;
    char serverPath[WS_GENERAL_LEN];

    EventCallback eventCallback;

    void *context;
} WstClient;

typedef enum {
    WST_SUCCESSFUL = 0,
    WST_INPUT_NULL = 1,
    WST_CREATE_CONTEXT_FAILED,
    WST_BUTT,
} ErrorCode;

typedef enum {
    WST_MSGTYPE_CONNECT_SUCCESS,
    WST_MSGTYPE_CONNECT_ERROR,
    WST_MSGTYPE_RECEIVED,
    WST_MSGTYPE_WRITEABLE
} WstClientMsgType;

int WstInit();

int WstConnect(WstClient *client);

int WstPoll(WstClient *client);

int WstSend(WstClient *wstClient);

int WstDisconnect(WstClient *client);

#endif // WS_CLIENT_INTERFACE_H