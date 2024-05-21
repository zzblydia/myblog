---
title:  "libwebsockets-build-on-ubuntu"
date:   2024-05-18 01:33:00 +0800
last_modified_at: 2024-05-18 02:27:00 +0800
categories: websocket
tags: libwebsockets
---

# libwebsockets v4.3.3 build on ubuntu24.04  


## 背景  
1. 集成libwebsockets作为客户端访问TTS, ASR服务  
2. 集成libwebsockets作为服务端模拟TTS, ASR服务端,进行性能压测.  


## 编译安装  

### 环境  
ubuntu-24.04-desktop-amd64  
```
sudo apt-get update  
sudo apt install build-essential checkinstall zlib1g-dev cmake -y  
```

通过包安装openssl库及开发包(或使用源码安装的指定版本openssl)  
```
sudo apt install openssl
sudo apt install libssl-dev
```


### 过程  
1. [下载源码](https://github.com/warmcat/libwebsockets/releases/tag/v4.3.3)

2. 编译  
```
tar zxvf libwebsockets-4.3.3.tar.gz
cd libwebsockets-4.3.3
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=DEBUG -DLWS_WITH_MINIMAL_EXAMPLES=ON
make
make install
```

3.结果  
在build/lib下生成libwebsockets.so  
在build/bin下生成minimal-examples里的各种测试进程  


## 参考链接:  
[libwebsockets README.build](https://github.com/warmcat/libwebsockets/blob/v4.3.3/READMEs/README.build.md)  