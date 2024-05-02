---
title:  "long ping with timestamp on windows"
date:   2023-12-26 21:26:26 +0800
last_modified_at: 2024-05-03 04:32:00 +0800
categories: windows
tags: 
  - windows
  - ping
---

# windows10下带时间戳长ping

## 背景
局域网有台老笔记本做下载服务器, 总是突然黑屏, 断网, 无法定位详细的异常时间, 所以写了个常ping局域网网关的脚本.  
实现生成的文件名记录系统开机时间, 通过查询ping记录获取异常时间点.  

## 使用方式(cmd内设置了网关ip和保存路径)
windows双击start_ping_gateway.cmd  

## 输出  
20240427_075500_ping_gateway.txt  
2024/5/3 4:19:38	来自 192.168.8.1 的回复: 字节=1000 时间<1ms TTL=64  
2024/5/3 4:19:39	来自 192.168.8.1 的回复: 字节=1000 时间<1ms TTL=64  
2024/5/3 4:19:40	来自 192.168.8.1 的回复: 字节=1000 时间<1ms TTL=64  


## 设置任务计划, 实现开机自启动, 后台运行  
1. 开始菜单---任务计划程序---Microsoft---创建基本任务  
2. 任务何时开始---计算机启动时---启动程序---选择cmd脚本  
3. 点击完成时,打开任务属性对话框---完成----不管用户是否登录都要运行---不存储密码---隐藏---windows10  

## 细节  
[long ping with timestamp on windows](https://github.com/zzblydia/myBlog/tree/master/windows/ping)  