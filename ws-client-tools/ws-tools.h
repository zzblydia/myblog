#ifndef WS_TOOLS_H
#define WS_TOOLS_H

// direction: 0 for self, 1 for peer
int ws_GetAddrInfo(int fd, int direction, char *ip, unsigned short *port);

#endif // WS_TOOLS_H
