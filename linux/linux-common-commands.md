# linux common commands  

## ls -lrth  
## strace  
```
strace -f -k -n -s 1000 -t -q -e trace=connect,socket -o ./strace.log -p PID  
```

## xargs  

## sed  

## awk  

## netstat  
netstat -tunlp | grep 53  

## ip  

### ip rule  
ip rule help  
ip rule show/list  
```
0:      from all lookup local   # 255 local table  
32766:  from all lookup main    # 254 main table 
32767:  from all lookup default # 253 default table

```

ip rule add from 192.168.23.62/24 dev eth1 table 238  

### ip route  
cat /etc/iproute2/rt_tables  

ip route help  
ip route list  

ip route add 0/0 via 192.168.23.1 dev eth1 table 238  
ip route add default via 192.168.23.1 dev eth1 table 238  
ip route list table 238  
```
default via 192.168.23.1 dev eth1 
```

ip route add 192.168.23.0/24 via 192.168.23.1 dev eth0 table 110  
ip route list dev eth0 table 110  
```
192.168.23.0/24 via 192.168.23.1 dev eth0
```

ip route del 192.168.23.0/24 via 192.168.127.2 dev eth0 table 110  
ip route del 192.168.23.0/24 dev eth0 table 110  


### ip addr  
ip addr add 192.168.23.36/24 brd 192.168.23.255 dev eth0  
ip addr show dev eth0  
ip addr del 192.168.23.36/24 dev eth0  

