---
title:  "Processing of network packets"
date:   2025-04-08 04:13:00 +0800
last_modified_at: 2025-04-08 05:18:00 +0800
categories: linux
tags: ebpf
published: false
---

# Processing of network packets on Linux  

<!-- 网络数据包在linux上的的处理过程 -->
<!-- 收到的udp消息从网卡到内核到进程套接字, 都经历了哪些处理过程, 每个处理点如果丢包, 有哪些现象, 如何定位丢包点 -->
<!-- tcpdump, iptables, tc filter, 自定义内核模块, 都位于哪个处理点 -->
<!-- 要过滤掉某个ip和port的sip消息中的options消息, 其他消息正常处理, ipables就做不到, 因为iptables不处理协议层的内容 -->

## background  
There is a process A running on linux machine `X(10.10.10.2)`, It listens to socket `10.10.10.2:8023` and processes udp messages.  
A client sends udp messages on linux machine `Y(10.10.10.3)` to `X(10.10.10.2:8023)`, tcpdump can capture the udp messages on X but the process A cannot receive the data.   

## observe  
`ifconfig` on machine X shows that the RX error 0 and dropped is increasing.  
`perf recod` on machine X shows that the dropping reason is no udp socket.  


<!-- ebfp程序的几个要求 -->
<!-- 1.收到指定ip和port的数据, 转换套接字, 比如10.10.10.2:8023分发到10.10.10.2:8024, 10.10.10.2:8025, 10.10.10.2:8026 -->
<!-- 2.能接收其他程序的消息, 实现配置的传递, 并发配置永久保存到文件 -->

## references  
[ebpf入门实践教程](https://eunomia.dev/zh/tutorials/20-tc/)  
