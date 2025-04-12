# tc_ingress_02  
未系统学习ebpf知识的情况, 通过需求推动,靠grok3完成代码.  

---

## 文件  
| 文件                        | 描述        |
| -----------------------     | ----------- |
| tc_ingress_02_kernel.c      | 内核态程序, 在tc ingress处理网络数据包, 编译成.o文件, 等待用户态进程加载                 |
| tc_ingress_02_user.c        | 用户态程序, 更新log map和转发规则map, 加载内核态ebpf文件到内核                           |
| tc_ingress_socket.c         | 提供tcp和udp的套接字监听                                                                 |

---

## 程序说明  

### 程序目标  
1.内核态程序, 做网络数据包的转发.  
2.用户态程序, 配置网络数据包的转发规则  
3.每一条转发规则包含 规则id, 数据包类型, 源ip和port, 目的ip和port, 目标ip和port.  
 - 如针对tcp报文, 源ip和port是 192.168.23.1:8023, 目的ip和port是 192.168.23.62:8023的数据, 如果匹配到转发规则, 则转发到192.168.23.62:18023.  
 - 如针对udp报文, 源ip和port是 192.168.23.1:8024, 目的ip和port是 192.168.23.62:8024的数据, 如果匹配到转发规则, 则转发到192.168.23.62:18024.  
 
### 程序环境
ubuntu 24.04  

apt install -y clang llvm libbpf-dev  
Ubuntu clang version 18.1.3 (1ubuntu1)  

### tc_ingress_02_kernel.c  

#### 编译方法  
```
clang -target bpf -O2 -g -I/usr/include/$(uname -m)-linux-gnu/ -c tc_ingress_02_kernel.c -o tc_ingress_02_kernel.o  
```

### tc_ingress_02_user.c  

#### 编译方法  
```
sudo gcc -g -o tc_ingress_02_user tc_ingress_02_user.c -I/usr/include/$(uname -m)-linux-gnu/ -L /usr/include/$(uname -m)-linux-gnu/ -lbpf -D_TC_INGRESS_02_MAIN
sudo ./tc_ingress_02_user

// 起监听端口号和更新map配置
sudo gcc -g -o tc_ingress_02_socket tc_ingress_socket.c tc_ingress_02_user.c -I/usr/include/$(uname -m)-linux-gnu/ -L /usr/include/$(uname -m)-linux-gnu/ -lbpf -lpthread
sudo ./tc_ingress_02_socket
```

#### 命令行操作  
```
sudo ./tc_ingress_02_kernel_02 ens33 &

sudo tc filter del dev ens33 ingress
sudo rm /sys/fs/bpf/forward_rules
sudo rm /sys/fs/bpf/log_enable_map
```
