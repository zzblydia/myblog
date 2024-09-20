## ·第1章 初识Docker 与容器
Linux 容器(Linux Containers, LXC) 技术  
LAMP (Linux+Apache+MySQL+PHP)

## ·第2章 核心概念与安装配置
镜像/容器/仓库  

目前Docker支持Docker 引擎、DockerHub 、Docker Cloud等多种服务。  
docker 引擎：包括支持在桌面系统或云平台安装Docker, 以及为企业提供简单安全
弹性的容器集群编排和管理；  
docker Hub: 官方提供的云托管服务，可以提供公有或私有的镜像仓库；  
dockerCloud ：官方提供的容器云服务，可以完成容器的部署与管理，可以完整地支
持容器化项目，还有CI 、CD 功能。  

社区版本每个季度(3 、6 、9 、12 月）会发行一次稳定(Stable) 版本。版本号
命名格式为“年份．月份＂，如2Ol8 年6 月发布的版本号为vl8~.06 。

**ubuntu**  
首先需要安装apt-transport-https 等软件包支持https 协议的源：  
sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common  
sudo apt-get update  
ubuntu获取发行版本号  
lsb_release -cs

### 2.3 配置docker服务
为了避免每次使用Docker 命令时都需要切换到特权身份，可以将当前用户加入安装中
自动创建的docker 用户组，代码如下：  
$ sudo usermod -aGdocker USER_NAME  
用户更新组信息，退出并重新登录后即可生效。

## ·第3章 使用Docker镜像
### 3.1 获取镜像
docker pull registerServer/repoName:TAG  
docker pull ubuntu:18.04

### 3.2 查看镜像
#### 3.2.1 查看本地镜像
docker image help
docker images
docker image ls
#### 3.2.2 给镜像打标签
docker tag SOURCE_IMAGE[:TAG] TARGET_IMAGE[:TAG]  
docker tag 0534d0f60d54 app03:5000/jdk:1.8.0
#### 3.2.3 获取镜像的详细信息
docker inspect [-f keyword] repoName:TAG
#### 3.2.4 查看镜像历史
docker history repoName:TAG

### 3.3 搜寻镜像
docker search [option] keyword  
docker search --filter=is-official=true nginx  
docker search --filter=stars=4 tensorflow  

查看仓库里镜像的所有tag  
https://hub.docker.com/search

### 3.4 删除和清理镜像
docker rmi IMAGE
docker image prune

### 3.5 创建镜像
#### 3.5.1 基于现有容器创建镜像
docker commit option container_id image(REPO:TAG)
#### 3.5.2 基于本地模板导入
cat ubuntu-18.04-x86_64-minimal.tar.gz | docker import - ubuntu:18.04
#### 3.5.3 基于Dockerfile创建

### 3.6 存出和载入镜像
docker save -o ubuntu_18.04.tar ubuntu:18.04  
docker load -i ubuntu_18.04.tar  
docker load < ubuntu_18.04.tar  

### 3.7 上传镜像

## ·第4章 操作Docker容器
docker container help
### 4.1 创建容器
#### 4.1.1 新建容器(P49)
docker pull ubuntu:22.04  
docker create -it ubuntu:22.04  
#### 4.1.2 启动容器
docker start container_id
#### 4.1.3 新建并启动容器
docker run -it ubuntu:22.04 /bin/bash

### 4.2 停止容器
#### 4.2.1 暂停容器
docker pause container_id
docker unpause container_id

#### 4.2.2 终止容器
docker stop container_id
docker restart container_id

### 4.3 进入容器
### 4.3.2 exec命令
docker exec -it container_id /bin/bash  

### 4.4 删除容器
docker rm container_id

### 4.5 导入和导出容器
#### 4.5.1 容器导出成容器快照
docker export -o ubuntu22.04.tar container_id
#### 4.5.2 容器快照导入成镜像
docker import ubuntu22.03.tar - test/ubuntu:v1.0

### 4.6 查看容器
#### 4.6.1 查看容器
docker container inspect container_id
#### 4.6.2 查看容器进程
docker top container_id
#### 4.6.3 查看容器统计信息
docker stat container_id

### 4.7 容器其他命令
#### 4.7.1 复制命令
docker cp -aL container_id:path dest_path  
docker cp -aL src_path container_id:path  
#### 4.7.2 查看变更
docker diff container_id
#### 4.7.3 查看端口映射
docker port container_id
#### 4.7.4 更新配置
docker update

### 4.8 本章小结
在生产环境中，为了提高容器的高可用性和安全性，一方面要合理使用资源限制参数来
管理容器的资源消耗；另一方面要指定合适的容器重启策略，来自动重启退出的容器。此外，还可以使用HAProxy 等辅助工具来处理负载均衡，自动切换故障的应用容器。

## ·第5章 访问Docker仓库
## ·第6章 Docker 数据管理
### 6.2 数据卷容器
docker run -it -v /dbdata --name dbdata ubuntu  
Unable to find image 'ubuntu:latest' locally

创建一个数据卷容器dbdata, 并在其中创建一个数据卷挂载到/dbdata:  
docker run -it -v /dbdata --name dbdata ubuntu:22.04  
/dbdata是在容器里的目录  
docker run -it --volumes-from dbdata --name db1 ubuntu:22.04

docker run -d --name db3 --volumes-from db1 ubuntu:22.04 命令执行完容器就停了  
docker run -it --name db4 --volumes-from db1 ubuntu:22.04
## ·第7章 端口映射与容器互联
## ·第8章 使用Dockerfile 创建镜像
