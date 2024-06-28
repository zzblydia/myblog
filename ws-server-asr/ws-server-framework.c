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
    data->msg_count = 0;

    int ret = lws_GetAddrInfo(wsi, 1, data->ip, &data->port);
    if (ret != 0) {
        lwsl_wsi_err(wsi, "lws_server_GetClientInfo failed");
        return -1;
    }
    lwsl_wsi_user(wsi, "client from %s:%u", data->ip, data->port);
    return 0;
}

int lws_server_callback_receive(struct lws *wsi, void *user, void *in, size_t len) {
    struct session_data *data = (struct session_data *) user;
    if (data == NULL) {
        lwsl_wsi_err(wsi, "data is NULL");
        return -1;
    }

    // 以收到的第一条消息决定业务类型
    if (data->msg_count == 0) {

    }

    data->msg_count++;
    return 0;
}

int lws_server_callback_write(struct lws *wsi, void *user, void *in, size_t len) {
    return 0;
}


static int
server_service_callback(struct lws *wsi, enum lws_callback_reasons reason, void *user, void *in, size_t len) {
    switch (reason) {
        case LWS_CALLBACK_ESTABLISHED:
            lws_server_callback_established(wsi, user);
            break;
        case LWS_CALLBACK_RECEIVE:
            lws_server_callback_receive(wsi, user, in, len);
            break;
        case LWS_CALLBACK_SERVER_WRITEABLE:
            lws_server_callback_write(wsi, user, in, len);
            break;
        default:
            break;
    }

    return 0;
}

struct lws_protocols protocols[] = {
        {
                "ws", server_service_callback, sizeof(struct session_data), MAX_PAYLOAD_SIZE, 0, NULL, 0
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
