---
title:  "openssl-build-install-on-ubuntu"
date:   2024-05-17 21:17:00 +0800
last_modified_at: 2024-05-18 01:22:00 +0800
categories: openssl
---

# openssl-3.0.12 源码安装 on ubuntu24.04  


## 背景  
需要安装自定义版本的openssl开发库 或 需要调试openssl库 


## 编译安装  

### 环境  
ubuntu-24.04-desktop-amd64  
```
sudo apt-get update
sudo apt install build-essential checkinstall zlib1g-dev -y
```

### 过程  
1. [下载源码](https://www.openssl.org/source)

2. 编译  
```
tar zxvf openssl-3.0.12.tar.gz  
cd openssl-3.0.12
./Configure --prefix=/opt/openssl --openssldir=/usr/local/ssl --debug
make
make test
sudo make install
```
Configure options说明:  
1) 当前版本使用./Configure, 与./config效果相同.  
2) --openssldir 用于存放配置文件, 以及默认证书和密钥存储. 默认值(Unix:/usr/local/ssl)  
3) --prefix 进程, 库, 头文件安装目录. 默认值(Unix:/usr/local)  
4) --debug 调试版本, 带符号表和不优化编译
5) --with-zlib-include=DIR --with-zlib-lib=LIB  
6) no-asm 不适用汇编  
7) no-shared 不生成动态库  
8) -g3 gcc编译选项, 表示生成最多的调试信息, 会覆盖-g(默认值-g2)  

3. 添加环境变量  
```
echo 'export OPENSSL_ROOT_DIR=/opt/openssl' | sudo tee -a /etc/profile
source /etc/profile
```

4. 检验  
```
openssl version
whereis openssl
```


## 参考链接:  
[openssl-3.0.12/INSTALL.md](https://github.com/openssl/openssl/blob/openssl-3.0.12/INSTALL.md)  
[wiki Compilation_and_Installation](https://wiki.openssl.org/index.php/Compilation_and_Installation)  