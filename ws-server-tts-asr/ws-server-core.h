#ifndef LIBWEBSOCKETS_WS_SERVER_CORE_H
#define LIBWEBSOCKETS_WS_SERVER_CORE_H

#include <libwebsockets.h>
#include "ws-tools.h"

#define MAX_PAYLOAD_SIZE 1024

struct session_data {
    int msg_count;
    unsigned char buf[LWS_PRE + MAX_PAYLOAD_SIZE];
    int len;

    char ip[INET6_ADDRSTRLEN]; // 用户客户端或者服务端, 记录客户端的ip和port
    unsigned short port;

    char traceId[TRACE_ID_LEN];
};

int lws_server_callback_established(struct lws *wsi, void *user);

int lws_server_callback_receive(struct lws *wsi, void *user, void *in, size_t len);

int lws_server_callback_writeable(struct lws *wsi, void *user, void *in, size_t len);

#endif //LIBWEBSOCKETS_WS_SERVER_CORE_H
