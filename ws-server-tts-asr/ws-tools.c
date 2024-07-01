#ifdef _WIN32

#include <ws2tcpip.h>

#else

#endif

#include <stdio.h>
#include "ws-tools.h"

#define TRACE_ID_LEN 20

int ws_GetAddrInfo(int fd, int direction, char *ip, unsigned short *port) {
    if (fd < 0 || ip == NULL || port == NULL) {
        return -1;
    }

    struct sockaddr addr;
    socklen_t addr_len = sizeof(addr);

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

int ws_GenerateTraceId(char *traceId, int len) {
    if (traceId == NULL || len < TRACE_ID_LEN) {
        return -1;
    }

    // 暂时以时间戳代替
    char timestamp[TRACE_ID_LEN];
    int ret;
#ifdef _WIN32
    SYSTEMTIME sys;
    GetLocalTime(&sys);
    ret = sprintf(timestamp, "%04d%02d%02d_%02d%02d%02d_%03d",
                  sys.wYear, sys.wMonth, sys.wDay, sys.wHour, sys.wMinute, sys.wSecond, sys.wMilliseconds);
#else
    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct tm *tm = localtime(&tv.tv_sec);
    ret = sprintf(timestamp, "%04d%02d%02d_%02d%02d%02d_%03d",
            tm->tm_year + 1900, tm->tm_mon + 1, tm->tm_mday, tm->tm_hour, tm->tm_min, tm->tm_sec, tv.tv_usec / 1000);
#endif
    return ret;
}