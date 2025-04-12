# tc_ingress_01  
未系统学习ebpf知识的情况, 通过需求推动,靠grok3完成代码.  

---

## 文件  
| 文件                        | 描述        |
| -----------------------     | ----------- |
| tc_ingress_01_kernel.c      | 内核态程序, 在tc ingress完成网络数据包处理, 使用命令行启动, 启动后设置map并pinned持久化 |
| tc_ingress_01_user.c        | 用户态程序, 启动后监听tcp和udp端口, 并更新map                                           |
| tc_ingress_socket.c         | 提供tcp和udp的套接字监听                                                                |

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

### tc_ingress_01_kernel.c  

#### 编译方法  
```
sudo clang -target bpf -O2 -g -I/usr/include/$(uname -m)-linux-gnu/ -c tc_ingress_01_kernel.c -o tc_ingress_01_kernel.o  
```

#### 命令行操作  
```
加载
sudo tc qdisc add dev ens33 clsact  
sudo tc filter add dev ens33 ingress bpf obj tc_ingress_01_kernel.o sec classifier

加载效果
sudo tc qdisc show dev ens33 clsact
sudo tc filter show dev ens33 ingress
sudo bpftool prog list
sudo bpftool prog show name tc_ingress_01

sudo bpftool map
sudo bpftool map dump id 216
sudo ls -al /sys/fs/bpf/tc/globals/forward_rules_01
sudo ls -al /sys/fs/bpf/tc/globals/log_switch_01

删除
sudo tc qdisc del dev ens33 clsact
sudo tc filter del dev ens33 ingress
```

```
// to test
sudo bpftool map update name log_enable_map key 0 0 0 0 value 1

sudo bpftool map update name forward_rules key 6 0 0 0 c0 a8 17 01 00 00 1f 57 c0 a8 17 3e 00 00 1f 57 value 1 c0 a8 17 3e 00 00 46 5f
key：protocol=6 (TCP), src_ip=c0a81701 (192.168.23.1), src_port=1f57 (8023), dst_ip=c0a8173e (192.168.23.62), dst_port=1f47 (8023)。
value：rule_id=1, target_ip=c0a8173e (192.168.23.62), target_port=465f (18023)

sudo bpftool map update name forward_rules key 17 0 0 0 c0 a8 17 01 00 00 1f 48 c0 a8 17 3e 00 00 1f 48 value 2 c0 a8 17 3e 00 00 46 60
key：protocol=17 (TCP), src_ip=c0a81701 (192.168.23.1), src_port=1f48 (8024), dst_ip=c0a8173e (192.168.23.62), dst_port=1f48 (8024)。
value：rule_id=2, target_ip=c0a8173e (192.168.23.62), target_port=4660 (18023)
```

#### 报错  
```
tc filter add dev ens33 ingress bpf obj tc_ingress_01_kernel.o sec classifier 加载报错,没有调试信息

libbpf: BTF is required, but is missing or corrupted.
ERROR: opening BPF object file failed
Unable to load program


clang -target bpf -O2 -g -I/usr/include/$(uname -m)-linux-gnu/ -c tc_ingress_01_kernel.c -o tc_ingress_01_kernel.o
sudo tc filter add dev ens33 ingress bpf obj tc_ingress_01_kernel.o sec classifier 
加-g调试 加载日志疯狂刷屏 加载失败 优化update_l4_checksum函数后解决

libbpf: BTF is required, but is missing or corrupted.
ERROR: opening BPF object file failed
Unable to load program
```

#### 日志  
```
sudo cat /sys/kernel/debug/tracing/trace
```

#### AI提示词
```
1. 我正在ubuntu24.04上使用clang编写两个ebpf程序, 一个内核态, 一个用户态
2.程序的功能是
内核态程序, 做网络数据包的转发.  
用户态程序, 配置网络数据包的转发规则  
每一条转发规则包含 规则id, 数据包类型, 源ip和port, 目的ip和port, 目标ip和port.  
 - 如针对tcp报文, 源ip和port是 192.168.23.1:8023, 目的ip和port是 192.168.23.62:8023的数据, 如果匹配到转发规则, 则转发到192.168.23.62:18023.  
 - 如针对udp报文, 源ip和port是 192.168.23.1:8024, 目的ip和port是 192.168.23.62:8024的数据, 如果匹配到转发规则, 则转发到192.168.23.62:18024.  

3. 我已经实现一部分代码, 请按照我的代码和我的指示, 逐步改进
```


### tc_ingress_01_user.c  

#### 编译和测试方法  
```
// 只更新map配置
sudo gcc -g -o tc_ingress_01_user tc_ingress_01_user.c -I/usr/include/$(uname -m)-linux-gnu/ -L /usr/include/$(uname -m)-linux-gnu/ -lbpf -D_TC_INGRESS_01_MAIN
sudo ./tc_ingress_01_user

// 起监听端口号和更新map配置
gcc -g -o tc_ingress_01_socket tc_ingress_socket.c tc_ingress_01_user.c -I/usr/include/$(uname -m)-linux-gnu/ -L /usr/include/$(uname -m)-linux-gnu/ -lbpf -lpthread
 sudo ./tc_ingress_01_socket
 
sudo netstat -tunlp | grep 18023
sudo netstat -tunlp | grep 18024

从另一台机器使用socat模拟发送tcp消息和udp消息
echo "Hello, this is a tcp message 20250412-124800" | socat - TCP4:192.168.23.62:8023,bind=192.168.23.52,sourceport=8023
echo "Hello, this is a udp message 20250412-125400" | socat - TCP4:192.168.23.62:8024,bind=192.168.23.52,sourceport=8024
```

#### AI提示词
```
1.我正在ubuntu使用tc filter ingress完成两个ebpf程序,一个内核态程序, 编译成.o后通过tc filter add 加载到内中, 生成了持久化的map log_switch_01和forward_rules_01 (通过sudo bpftool map查询), 
现在在写用户态程序, 想更新持久化map的值
```

#### bug  
1.重复执行,会重复添加配置.  

