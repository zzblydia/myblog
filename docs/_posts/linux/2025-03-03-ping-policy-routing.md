#  Experience with policy routing  
I encountered a problem where I couldn't ping, and then I experienced policy routing. Now the simplified scenario is as follows.  


## The basic network environment  
my computer A can reach subnet `172.90.185.0/24` with ip `172.136.125.70` by **switch**.  
my computer A can reach subnet `100.61.193.0/24` with ip `100.255.200.8`  by using **vpn**.  

## The problem  
Machine M with `eth0 172.90.185.65` and `eth1 100.61.193.131`. I can ping `172.90.185.65` success but cannot ping `100.61.193.131` successfully.  
Machine N with `eth0 100.61.193.109` and `eth1 172.90.185.59`. I can ping `100.61.193.109` success but cannot ping `172.90.185.59` successfully.  
It seems that I can never ping the IP address on the second network card.  

run command `route` on M:
```
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
default         172.90.185.1     0.0.0.0         UG    0      0        0 eth0
172.90.185.0     *               255.255.255.0   U     0      0        0 eth0
100.61.193.0     *               255.255.255.0   U     0      0        0 eth1
```

run command `route` on N:
```
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
default         100.61.193.1     0.0.0.0         UG    0      0        0 eth0
172.90.185.0     *               255.255.255.0   U     0      0        0 eth1
100.61.193.0     *               255.255.255.0   U     0      0        0 eth0
```

## Explore  
Later some application add ip `100.61.193.40` on `eth1:0` of M, and I can ping `100.61.193.40` from A successfully. I decided to find out.  

I am using `tcpdump -i any -s 0 icmp` to capture packets on machine **M**:  
When I ping 172.90.185.65 from A, the source IP of the packets is 172.136.125.70.  
When I ping 100.61.193.40 from A, the source IP of the packets is 100.255.200.8."  

## Command `ip`   
Using `ip rule list all` to view all rules, I found that `100.61.193.40` has special handling and will use `routing table 239`.
```
32755:  from 100.61.193.40 lookup 239
```

Run command `ip route list table 239` and view the processing action of route table 239:  
```
default via 100.61.193.1 dev eth1
```

Make the similiar **rule** and `route` for `100.61.193.131`  
```
ip rule add from 100.61.193.131 table 230
ip route add default via 100.61.193.1 dev eth1 table 230 
```

then ping `100.61.193.131` from A successed and ping `100.255.200.8 -I 100.61.193.131` also succeed.

## Other
Run `ping 100.255.200.8` from M failed, and run `ping 100.255.200.8 -I eth1` from also failed.  
add route to table main `ip route add 100.255.200.8/32 via 100.61.193.1 dev eth1` and it succeed.
