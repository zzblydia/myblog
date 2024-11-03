#include "ws-client-interface.h" // for WstClient
#include "ws-utils.h"
#include "ws-client-core.h"

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

int ws_client_callback_protocol_init(struct lws *wsi, void *user) {
    struct lws_context *context = lws_get_context(wsi);
    WstClient *wstClient = (WstClient *) lws_context_user(context);

    char addr_port[256] = {0};
    sprintf(addr_port, "%s:%u", wstClient->serverAddress, wstClient->serverPort);

    // 客户端连接参数
    struct lws_client_connect_info conn_info = {0};
    conn_info.context = context;
    conn_info.address = wstClient->serverAddress;
    conn_info.port = wstClient->serverPort;
    conn_info.host = addr_port;
    conn_info.origin = addr_port;
    conn_info.protocol = g_protocols[0].name;

    if (wstClient->ssl) {
        conn_info.ssl_connection =
                LCCSCF_USE_SSL | LCCSCF_ALLOW_SELFSIGNED | LCCSCF_SKIP_SERVER_CERT_HOSTNAME_CHECK |
                LCCSCF_ALLOW_INSECURE;
    }

    lws_client_connect_via_info(&conn_info);
    return WST_SUCCESSFUL;
}

int ws_client_callback_established(struct lws *wsi, void *user) {
    struct session_data *data = (struct session_data *) user;
    if (data == NULL) {
        lwsl_wsi_err(wsi, "data is NULL");
        return -1;
    }

    int fd = lws_get_socket_fd(wsi);
    if (fd < 0) {
        lwsl_wsi_err(wsi, "lws_get_socket_fd failed");
        return -1;
    }
    int ret = ws_GetAddrInfo(fd, 0, data->ip, &data->port);
    if (ret != 0) {
        lwsl_wsi_err(wsi, "lws_server_GetClientInfo failed");
        return -1;
    }
    lwsl_wsi_user(wsi, "client with %s:%u", data->ip, data->port);
    return WST_SUCCESSFUL;
}

int ws_client_callback(struct lws *wsi, enum lws_callback_reasons reason, void *user, void *in, size_t len) {
    struct session_data *data = (struct session_data *) user;
    struct lws_context *context = lws_get_context(wsi);
    lwsl_cx_user(context, "reason %d", reason);

    switch (reason) {
        case LWS_CALLBACK_PROTOCOL_INIT:
            ws_client_callback_protocol_init(wsi, user);
            break;
        case LWS_CALLBACK_CLIENT_ESTABLISHED:   // 连接到服务器后的回调
            ws_client_callback_established(wsi, user);
            break;
        case LWS_CALLBACK_CLIENT_RECEIVE:       // 接收到服务器数据后的回调，数据为in，其长度为len
            lwsl_notice("receive: %s\n", (char *) in);
            break;
        case LWS_CALLBACK_CLIENT_WRITEABLE:     // 当此客户端可以发送数据时的回调
            if (data->msg_count < 3) {
                // 前面LWS_PRE个字节必须留给LWS
                memset(data->buf, 0, sizeof(data->buf));
                char *msg = (char *) &data->buf[LWS_PRE];
                data->len = sprintf(msg, "hello %d", data->msg_count);
                lwsl_notice("send: %s\n", msg);

                // 通过WebSocket发送文本消息
                lws_write(wsi, &data->buf[LWS_PRE], (size_t) data->len, LWS_WRITE_TEXT);

                data->msg_count++;
            }
            break;
        default:
            break;
    }
    return 0;
}

int http_client_callback(struct lws *wsi, enum lws_callback_reasons reason, void *user, void *in, size_t len) {
    struct lws_context *context = lws_get_context(wsi);
    lwsl_cx_user(context, "reason %d", reason);
    return 0;
}

struct lws_protocols g_protocols[] = {
        {
                "ws", ws_client_callback, sizeof(struct session_data),
                MAX_PAYLOAD_SIZE, 0, NULL, 0
        },
        {
                "http", http_client_callback, sizeof(struct session_data),
                MAX_PAYLOAD_SIZE, 0, NULL, 0
        },
        LWS_PROTOCOL_LIST_TERM
};