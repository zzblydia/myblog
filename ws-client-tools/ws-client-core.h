#ifndef WS_CLIENT_CORE_H
#define WS_CLIENT_CORE_H

#include <libwebsockets.h>

#define MAX_PAYLOAD_SIZE 10240
#define TRACE_ID_MAX_LEN (32 + 1)

struct session_data {
    int msg_count;
    unsigned char buf[LWS_PRE + MAX_PAYLOAD_SIZE];
    int len;

    char ip[INET6_ADDRSTRLEN]; // 用户客户端或者服务端, 记录客户端的ip和port
    unsigned short port;

    char traceId[TRACE_ID_MAX_LEN];
};

int ws_client_callback(struct lws *wsi, enum lws_callback_reasons reason, void *user, void *in, size_t len);

int ws_client_callback_protocol_init(struct lws *wsi, void *user);

int ws_client_callback_established(struct lws *wsi, void *user);

extern struct lws_protocols g_protocols[];

#endif // WS_CLIENT_CORE_H
