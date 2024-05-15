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
TODO  
&nbsp;

6) 用户自定义数据什么时候初始化的?  
struct session_data *data = (struct session_data *) user;  
&nbsp;
