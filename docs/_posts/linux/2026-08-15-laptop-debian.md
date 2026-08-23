---
title:  "深度使用Debian"
date:   2026-08-15 06:20:00 +0800
last_modified_at: 2026-08-15 09:57:00 +0800
categories: linux
tags: debian
---

笔记本电脑安装使用Debian13.6 trixie

**最终背叛了Ubuntu 22.04 选择了Debian 13.6 哈哈哈 后悔死我了没早点换 新系统太爽了 笑出声**  
因为Ubuntu系统里已经配置了开发环境,在鼓起勇气换系统前问了Gemini和Claude很多次更换系统的风险和收益,最终还是决定梭一把  

## 背景
[前情提要](https://zzblydia.github.io/myblog/linux/laptop-ubuntu/)  

## 后期体验  
### 20260820
1.`fcitx5`输入法非常好用,中英文切换简单， 联想词汇多，没有副作用，不会出现`门`字显示异常。  
2.各类软件(vscode cursor chrome)暂时没有出现过coredump，甚至软件商店还能检测更新这些软件了。  
3.习惯了没有任务栏，应用都是全屏，切换应用习惯了用windows键而不是Tab。  
4.再也不用因为不了解细节纠结使用`Ubuntu`还是`Debian`了，后者拥抱`non-free`软件源后我选择无条件使用。  

## 安装记录  
1.在Windows环境使用`Ventoy`制作多系统启动U盘,并把镜像`debian-13.6.0-amd64-DVD-1.iso`放进去  
2.在笔记本电脑A上使用VMware Workstation安装了一把测试镜像没有问题  
3.修改笔记本电脑B的BIOS系统顺序,调整启动顺序,U盘启动第一位  
**4.安装语言English,键盘选择Singapore,不使用网络镜像(net mirror),会跳过主机名设置**  
5.安装后进入系统,能正常连接wifi,触摸板正常,键盘正常  
6.刚开始桌面左侧没有快捷方式,还有点不习惯  
7.最大的提升是放弃了输入法`IBus`,而选择了`fcitx5`  

安装后截图:  
![安装完成重启后进入桌面的截图]({{ site.baseurl }}/assets/images/debian13.6_finish_install_reboot.png)

## 安装后配置
### 1.配置非自由软件源  
创建`/etc/apt/sources.list.d/debian.sources`并粘贴如下:  
(系统默认安装的`vim-tiny`,如果不会用就切换到root用`echo`把内容输进去)
```
Types: deb deb-src
URIs: http://deb.debian.org/debian
Suites: trixie trixie-updates trixie-security
Components: main non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
```
然后执行`sudo apt update`  

### 2.安装软件  

#### vim
```
dpkg -l | grep vim
sudo apt remove vim-tiny vim-common
sudo apt install vim
```

#### fcitx5  
```
sudo apt install fcitx5 fcitx5-pinyin fcitx5-chinese-addons
```
安装完后不用按教程配置环境变量,直接在机器上搜索`Fcitx 5 Configuration`配置就行  
注意不要选择`Keyboard-Chinese-Hanyu Pinyin letters(with AltGr dead keys)`  
安装后截图:  
![fcitx5 配置界面截图]({{ site.baseurl }}/assets/images/fcitx5_configuration.png)

#### npm
```
# 1. 确保 keyrings 目录存在并下载 NodeSource GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg

# 2. 清理旧格式的配置文件(如果之前生成过)
sudo rm -f /etc/apt/sources.list.d/nodesource.list

# 3. 使用 DEB822 格式写入 /etc/apt/sources.list.d/nodesource.sources
sudo tee /etc/apt/sources.list.d/nodesource.sources > /dev/null <<EOF
Types: deb
URIs: https://deb.nodesource.com/node_24.x
Suites: nodistro
Components: main
Signed-By: /etc/apt/keyrings/nodesource.gpg
EOF

# 4. 更新软件源并安装/升级
sudo apt update
sudo apt install -y nodejs
```  
#### Docker CE  
```
# Add Docker's official GPG key:
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
```

```
# 最新版本
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 指定版本
apt list --all-versions docker-ce
docker-ce/trixie 5:29.7.1-1~debian.13~trixie amd64
docker-ce/trixie 5:29.7.0-1~debian.13~trixie amd64

VERSION_STRING=5:29.7.1-1~debian.13~trixie
sudo apt install docker-ce=$VERSION_STRING docker-ce-cli=$VERSION_STRING containerd.io docker-buildx-plugin docker-compose-plugin
```

```
# 安装后
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
docker run hello-world

sudo vi /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

#### tcpdump  
```
sudo apt install tcpdump

# 普通用户也能使用
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/tcpdump
```

#### others
```
telegram
chrome
cursor
vscode
claude
opencode
deepseek-ai/dsh
btop
```
