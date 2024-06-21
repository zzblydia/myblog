#ifndef LIBWEBSOCKETS_WS_SERVER_CORE_H
#define LIBWEBSOCKETS_WS_SERVER_CORE_H

#include <libwebsockets.h>

// direction: 0 for self, 1 for peer
int lws_GetAddrInfo(struct lws *wsi, int direction, char *ip, unsigned short *port);

#endif //LIBWEBSOCKETS_WS_SERVER_CORE_H
