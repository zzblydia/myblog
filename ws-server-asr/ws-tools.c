#include "ws-tools.h"

int lws_GetAddrInfo(struct lws *wsi, int direction, char *ip, unsigned short *port) {
    if (wsi == NULL || ip == NULL || port == NULL) {
        return -1;
    }
    struct sockaddr addr;
    socklen_t addr_len = sizeof(addr);
    int fd = lws_get_socket_fd(wsi);
    if (fd < 0) {
        lwsl_wsi_err(wsi, "lws_get_socket_fd failed");
        return -1;
    }

    if (direction == 0) {
        getsockname(fd, (struct sockaddr *) &addr, &addr_len);
    } else {
        getpeername(fd, (struct sockaddr *) &addr, &addr_len);
    }

    if (addr.sa_family == AF_INET) {
        struct sockaddr_in *s = (struct sockaddr_in *) &addr;
        *port = ntohs(s->sin_port);
        inet_ntop(AF_INET, &s->sin_addr, ip, INET6_ADDRSTRLEN);
    } else { // AF_INET6
        struct sockaddr_in6 *s = (struct sockaddr_in6 *) &addr;
        *port = ntohs(s->sin6_port);
        inet_ntop(AF_INET6, &s->sin6_addr, ip, INET6_ADDRSTRLEN);
    }
    return 0;
}