#include "ws-server-core.h"

int lws_server_callback_established(struct lws *wsi, void *user) {
    struct session_data *data = (struct session_data *) user;
    if (data == NULL) {
        lwsl_wsi_err(wsi, "data is NULL");
        return -1;
    }
    data->msg_count = 0;
    int fd = lws_get_socket_fd(wsi);
    if (fd < 0) {
        lwsl_wsi_err(wsi, "lws_get_socket_fd failed");
        return -1;
    }

    int ret = ws_GetAddrInfo(fd, 1, data->ip, &data->port);
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

int lws_server_callback_writeable(struct lws *wsi, void *user, void *in, size_t len) {
    return 0;
}