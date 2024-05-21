---
title:  "libwebsockets-IP-address-mismatch"
date:   2024-05-20 18:19:00 +0800
last_modified_at: 2024-05-18 02:32:00 +0800
categories: websocket
tags:
  - libwebsockets
  - openssl
---

# SSL error: IP address mismatch (preverify_ok=0;err=64;depth=0)  


## 问题  
集成libwebsockets作为测试客户端和测试服务端进行websockets通信.  

测试服务端使用的证书是libwebsockets cmake默认生成的libwebsockets-test-server.pem,  
SSL加密时ssl_connection未启用LCCSCF_SKIP_SERVER_CERT_HOSTNAME_CHECK, 连接服务端时报错:  
**E: SSL error: IP address mismatch (preverify_ok=0;err=64;depth=0)**  
E: CLIENT_CONNECTION_ERROR  


## 探索
看到这个报错时, 我感到强烈的好奇, 既然说是ip地址不匹配, 那是哪两个字符串不匹配呢, 代码里一定有类似strcmp的操作.  
根据libwebsockets的源码发现报错的函数是OpenSSL_client_verify_callback, 这是一个ssl证书校验的回调函数.  
[源码编译openssl-3.0.12带符号表版本](https://zzblydia.github.io/myBlog/openssl/openssl-build-install/), 对测试客户端进行gdb调试获取调用栈:  
```
#0  OpenSSL_client_verify_callback (preverify_ok=0, x509_ctx=0x55555564cfd0) at /opt/packages/libwebsockets/lib/tls/openssl/openssl-client.c:93
#1  verify_cb_cert (ctx=0x55555564cfd0, x=0x555555646460, depth=0, err=64) at crypto/x509/x509_vfy.c:163
#2  check_id_error (ctx=0x55555564cfd0, errcode=64) at crypto/x509/x509_vfy.c:767
#3  check_id (ctx=0x55555564cfd0) at crypto/x509/x509_vfy.c:803
#4  verify_chain (ctx=0x55555564cfd0) at crypto/x509/x509_vfy.c:219
#5  X509_verify_cert (ctx=0x55555564cfd0) at crypto/x509/x509_vfy.c:295
#6  ssl_verify_cert_chain (s=0x55555563ec40, sk=0x555555636630) at ssl/ssl_cert.c:446
#7  tls_post_process_server_certificate (s=0x55555563ec40, wst=WORK_MORE_A) at ssl/statem/statem_clnt.c:1870
#8  ossl_statem_client_post_process_message (s=0x55555563ec40, wst=WORK_MORE_A) at ssl/statem/statem_clnt.c:1085
#9  read_state_machine (s=0x55555563ec40) at ssl/statem/statem.c:675
#10 state_machine (s=0x55555563ec40, server=0) at ssl/statem/statem.c:442
#11 ossl_statem_connect (s=0x55555563ec40) at ssl/statem/statem.c:265
#12 SSL_do_handshake (s=0x55555563ec40) at ssl/ssl_lib.c:3937
#13 SSL_connect (s=0x55555563ec40) at ssl/ssl_lib.c:1759
#14 lws_tls_client_connect (wsi=0x555555634130, errbuf=0x7fffffffda10 "*", elen=128) at /opt/packages/libwebsockets/lib/tls/openssl/openssl-client.c:525
#15 lws_ssl_client_connect2 (wsi=0x555555634130, errbuf=0x7fffffffda10 "*", len=128) at /opt/packages/libwebsockets/lib/tls/tls-client.c:63
#16 lws_http_client_socket_service (wsi=0x555555634130, pollfd=0x5555555d7430) at /opt/packages/libwebsockets/lib/roles/http/client/client-http.c:205
#17 rops_handle_POLLIN_h1 (pt=0x5555555d4520, wsi=0x555555634130, pollfd=0x5555555d7430) at /opt/packages/libwebsockets/lib/roles/h1/ops-h1.c:701
#18 lws_service_fd_tsi (context=0x5555555d42a0, pollfd=0x5555555d7430, tsi=0) at /opt/packages/libwebsockets/lib/core-net/service.c:766
#19 _lws_plat_service_forced_tsi (context=0x5555555d42a0, tsi=0) at /opt/packages/libwebsockets/lib/plat/unix/unix-service.c:51
#20 _lws_plat_service_tsi (context=0x5555555d42a0, timeout_ms=2000000000, tsi=0) at /opt/packages/libwebsockets/lib/plat/unix/unix-service.c:216
#21 lws_plat_service (context=0x5555555d42a0, timeout_ms=0) at /opt/packages/libwebsockets/lib/plat/unix/unix-service.c:235
#22 lws_service (context=0x5555555d42a0, timeout_ms=0) at /opt/packages/libwebsockets/lib/core-net/service.c:838
#23 main () at /opt/packages/libwebsockets/minimal-examples/ws-client/ws-client-simple-send-recv-tls/ws-client-simple-send-recv-tls.c:103
```
测试客户端调用ssl库进行证书校验, 走读openssl check_id相关代码发现在函数do_x509_check中,  
会读取服务端(交换的)证书libwebsockets-test-server.pem中的**X509v3 Subject Alternative Name**扩展字段,  
并根据字段前缀类型(mail/dns/ip)与客户连接信息结构体**lws_client_connect_info中的host**字符串做对比.  


## 验证  
输出libwebsockets-test-server.pem的内容, 发现并没有这个扩展字段.  
```
X509v3 extensions:
            X509v3 Subject Key Identifier: 
                76:F2:98:1A:BB:CA:E5:5F:F2: ...
            X509v3 Authority Key Identifier: 
                76:F2:98:1A:BB:CA:E5:5F:F2: ...
            X509v3 Basic Constraints: critical
                CA:TRUE
```

生成带有这个扩展字段的证书, 并**重启服务端以使用新证书**, 再次使用客户端进行连接, 发现连接成功.  
```
X509v3 extensions:
            X509v3 Subject Alternative Name: 
                IP Address:192.168.23.11
            X509v3 Subject Key Identifier: 
                A5:10:70:2D:17:40:18:1F:0D: ...
```


## 细节  
[ws-client-simple-send-recv-tls](https://github.com/zzblydia/libwebsockets/tree/v4.3-stable/minimal-examples/ws-client/ws-client-simple-send-recv-tls)  
[ws-server-simple-send-recv-tls](https://github.com/zzblydia/libwebsockets/tree/v4.3-stable/minimal-examples/ws-server/ws-server-simple-send-recv-tls)  


## 相关  
[libwebsockets issue #3000](https://github.com/warmcat/libwebsockets/issues/3000)  
[libwebsockets issue #1826](https://github.com/warmcat/libwebsockets/issues/1826)  