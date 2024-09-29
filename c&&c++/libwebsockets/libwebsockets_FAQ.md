# 使用记录 #

## 1. 使用疑问  

1) 如何在回调时使用连接时传入的自定义数据  
struct lws_context_creation_info user 指向自定义结构体  
&nbsp;

2) 作为http client时, 接收的response header 过长  
修改 struct lws_context_creation_info max_http_header_data  
&nbsp;

3) 作为ws client时, 携带的request header 过长  
修改 struct lws_context_creation_info pt_serv_buf_size  
&nbsp;

4) 日志如何重定向到文件? 不同的会话如何重定向到不同文件?  
TODO  
&nbsp;

5) 客户端可以指定client port吗? 如果不指定, 如何在连接后获取客户端建链使用的随机端口? 服务端呢?  
bind client port 在 [v4.3-stable分支不支持, main分支代码支持](https://github.com/warmcat/libwebsockets/issues/3150)   
客户端可以在`LWS_CALLBACK_CLIENT_ESTABLISHED`回调中获取客户端建链使用的随机端口, 使用的结构体成员为`struct lws`的`sa46_local`成员  
注意处理端口时把网络序转换成字节序, 参照`lws_socket_bind`中的`port = ntohs(sain.sin_port);`  
&nbsp;

6) 用户自定义数据什么时候初始化的?  
struct session_data *data = (struct session_data *) user;  
&nbsp;

7) 一个context与多个连接的关系  
多个连接是可以使用同一个context的, 疑问是:  
poll一个context时, 多个连接的回调事件是如何处理的?  
是按事件到来的先后顺序吗?会不会出现一直处理一个连接的情况?  
&nbsp;

8) LWS_CALLBACK_PROTOCOL_INIT  
如果直接进行连接, 则在`lws_client_connect_via_info`中产生回调  
否则在`lws_service_adjust_timeout`中产生回调  
&nbsp;

9) lws_service立刻返回
业务场景有多个context在同一个线程里依次poll,如果没有事件需要立即返回.  
此时通过设置`lws_service(context, -1);`实现  
&nbsp;

10) lws_client_connect_via_info的调用时机  
可以在`lws_create_context`之后调用, 也可以在`LWS_CALLBACK_PROTOCOL_INIT`里调用  
二者有什么讲究呢?  
目前看需要自动重连, 则可以放在`LWS_CALLBACK_PROTOCOL_INIT`里  
&nbsp;

11) 使用域名连接服务器时, 会在每次连接时向dns服务器发送请求  
并发量比较高时, 可能dns服务器会响应错误或者响应不及时.
另外调用查询dns时调用系统函数getaddrinfo(底层调用poll,可用strace跟踪发现)会阻塞.
```
#0 getaddrinfo
#1 lws_getaddrinfo46
#2 lws_client_connect_2_dnsreq  
```

12) 生产环境使用的cmake编译选项  
cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_VERBOSE_MAKEFILE=ON  
不使用-DCMAKE_BUILD_TYPE=DEBUG是因为不使用断言assert  
不使用-DCMAKE_BUILD_TYPE=RELEASE是因为编译选项(可能)会启用-O3优化且不带-g(使用strip剥离调试信息)  
使用-DCMAKE_BUILD_TYPE=RelWithDebInfo的(可能的)编译选项为-O2 -g  
&nbsp;

13) wsi双重释放导致进程core  
触发场景:在回调函数收到LWS_CALLBACK_CLIENT_CONNECTION_ERROR事件时调用lws_context_destroy  


