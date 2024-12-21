# mrcp nlr server demo for performance  

## 用法  
nohup ./mrcp_nlr_server ip port  >./nlr.log 2>&1 &  
ip默认127.0.0.1  
port默认9000  

## 实现原理
 - 收到 DEFINE-GRAMMAR, 回复200. (事务id与请求中保持一致)  
 - 收到 RECOGNIZE, 回复200, 1秒后回复 START_OF_SPEECH, 然后每隔1秒回复一次 INTERMEDIATE-RESULT(共5次)  
 - 收到 STOP, 回复200.
