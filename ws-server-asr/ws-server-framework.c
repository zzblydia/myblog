#include <libwebsockets.h>
#include <signal.h>
#include "ws-tools.h"

static volatile int exit_sig = 0;
#define MAX_PAYLOAD_SIZE 1024

void signal_handle(int sig) {
    lwsl_notice("receive signal %d", sig);
    exit_sig = 1;
}

struct session_data {
    int msg_count;
    unsigned char buf[LWS_PRE + MAX_PAYLOAD_SIZE];
    int len;

    char ip[INET6_ADDRSTRLEN]; // 用户客户端或者服务端, 记录客户端的ip和port
    unsigned short port;

    char traceId[128];
};

int lws_server_callback_established(struct lws *wsi, void *user) {
    struct session_data *data = (struct session_data *) user;
    if (data == NULL) {
        lwsl_wsi_err(wsi, "data is NULL");
        return -1;
    }

    int ret = lws_GetAddrInfo(wsi, 1, data->ip, &data->port);
    if (ret != 0) {
        lwsl_wsi_err(wsi, "lws_server_GetClientInfo failed");
        return -1;
    }
    lwsl_wsi_user(wsi, "client from %s:%u", data->ip, data->port);
    return 0;
}

static int server_simple_callback(struct lws *wsi, enum lws_callback_reasons reason, void *user, void *in, size_t len) {
    struct session_data *data = (struct session_data *) user;
    switch (reason) {
        case LWS_CALLBACK_ESTABLISHED:
            lws_server_callback_established(wsi, user);
            break;
        case LWS_CALLBACK_RECEIVE:           // 当接收到客户端发来的数据以后
            // 下面的调用禁止在此连接上接收数据
            //lws_rx_flow_control(wsi, 0);

            // 保存客户端发来的消息
            memcpy(&data->buf[LWS_PRE], in, len);
            data->len = (int) len;
            lwsl_notice("received message:%s\n", (char *) &data->buf[LWS_PRE]);

            // 触发一次写回调, 给客户端应答
            lws_callback_on_writable(wsi);
            break;
        case LWS_CALLBACK_SERVER_WRITEABLE:   // 当此连接可写时
            lwsl_notice("send back message:%s\n", (char *) &data->buf[LWS_PRE]);
            lws_write(wsi, &data->buf[LWS_PRE], (size_t) data->len, LWS_WRITE_TEXT);

            // 下面的调用允许在此连接上接收数据
            // lws_rx_flow_control(wsi, 1);
            break;
        default:
            break;
    }

    return 0;
}

struct lws_protocols protocols[] = {
        {
                "ws", server_simple_callback, sizeof(struct session_data), MAX_PAYLOAD_SIZE, 0, NULL, 0
        },
        LWS_PROTOCOL_LIST_TERM
};

int main(int argc, char **argv) {
    signal(SIGTERM, signal_handle);

    // 以便使用 lwsl_wsi_user
    int logs = LLL_USER | LLL_ERR | LLL_WARN | LLL_NOTICE;
    lws_set_log_level(logs, NULL);

    struct lws_context_creation_info ctx_info = {0};
    ctx_info.port = 8002;
    ctx_info.iface = NULL;
    ctx_info.protocols = protocols;

    // SSL加密, 设置证书和私钥
    ctx_info.options |= LWS_SERVER_OPTION_DO_SSL_GLOBAL_INIT;
    ctx_info.ssl_cert_filepath = "../libwebsockets-test-server.pem";
    ctx_info.ssl_private_key_filepath = "../libwebsockets-test-server.key.pem";

    struct lws_context *context = lws_create_context(&ctx_info);
    while (!exit_sig) {
        lws_service(context, 0);
    }
    lws_context_destroy(context);

    return 0;
}