#include <signal.h>
#include "ws-server-core.h"

static volatile int exit_sig = 0;

void signal_handle(int sig) {
    lwsl_notice("receive signal %d", sig);
    exit_sig = 1;
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
            lws_server_callback_writeable(wsi, user, in, len);
            break;
        default:
            break;
    }

    return 0;
}

struct lws_protocols g_protocols[] = {
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
    ctx_info.protocols = g_protocols;

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
