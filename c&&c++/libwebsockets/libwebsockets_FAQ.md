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
如果直接进行连接, 则在lws_client_connect_via_info中产生回调  
否则在lws_service_adjust_timeout中产生回调  