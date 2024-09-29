#include "ws-client-interface.h" // for WstClient
#include "ws-tools.h"
#include "ws-client-core.h"

struct lws_protocols g_protocols[] = {
        {
                //协议名称，协议回调，接收缓冲区大小
                "ws", ws_client_callback, sizeof(struct session_data),
                MAX_PAYLOAD_SIZE, 0, NULL, 0
        },
        LWS_PROTOCOL_LIST_TERM
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

    // 创建一个客户端连接
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