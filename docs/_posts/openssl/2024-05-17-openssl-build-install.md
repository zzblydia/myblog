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
<!--
| Configure options        | 说明              
|:-------------------------|:------------------  
| ./Configure              | 与./config效果相同  
| --openssldir             | 用于存放配置文件, 以及默认证书和密钥存储. 默认值(Unix:/usr/local/ssl)  
| --prefix                 | 进程, 库, 头文件安装目录. 默认值(Unix:/usr/local)  
| --debug                  | 调试版本, 带符号表(-g)和不优化编译(-O0)  
| --with-zlib-include=DIR  | 指定zlib头文件目录  
| --with-zlib-lib=LIB      | 指定zlib库目录  
| no-asm                   | 不使用汇编  
| no-shared                | 不生成动态库  
| -g3                      | gcc编译选项, 表示生成最多的调试信息, 会覆盖-g(默认值-g2)  
-->
Configure options说明:  
1) 当前版本使用./Configure, 与./config效果相同.  
2) --openssldir 用于存放配置文件, 以及默认证书和密钥存储. 默认值(Unix:/usr/local/ssl)  
3) --prefix 进程, 库, 头文件安装目录. 默认值(Unix:/usr/local)  
4) --debug 调试版本, 带符号表和不优化编译  
5) --with-zlib-include=DIR --with-zlib-lib=LIB 连接zlib库  
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


## 报错  
build openssl-1.1.1m时偶然遇到如下报错, 发现是生成libcrypto.so时报错, 观察编译时已经使用了-fPIC参数  
```
/usr/bin/ld: crypto/bn/x86_64-mont.o: relocation R_X86_64_PC32 against undefined symbol `bn_sqrx8x_internal' can not be used when making a shared object; recompile with -fPIC
```

遂尝试增加配置参数no-shared不生成.so, 发现生成静态库依然报错  
```
/opt/packages/openssl-1.1.1m/crypto/bn/x86_64-mont.s:781: undefined reference to `bn_sqrx8x_internal'
```
但终于发现是编译x86_64-mont.pl成x86_64-mont.s时报错, 遂增加no-asm参数, 最后问题规避(未根本解决).  


## 参考链接:  
[openssl-3.0.12/INSTALL.md](https://github.com/openssl/openssl/blob/openssl-3.0.12/INSTALL.md)  
[wiki Compilation_and_Installation](https://wiki.openssl.org/index.php/Compilation_and_Installation)  