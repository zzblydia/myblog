---
title:  "dns server with bind9"
date:   2024-12-04 20:05:00 +0800
last_modified_at: 2024-12-04 22:05:00 +0800
categories: dns
tags: bind9
---

# dns server with bind9  

## 1. install on ubuntu  
bind: Berkeley Internet Name Domain  
```
sudo apt-get install bind  
systemctl status named  
systemctl restart named  
```

## 2. configuration
target domain:  goodluck.com  
target ip:      192.168.23.62  
dns machine:    192.168.23.52  

**sudo vi /etc/bind/named.conf.local**  
```
zone "goodluck.com" {
    type master;
    file "/etc/bind/db.goodluck.com";
};
```

**sudo vi db.goodluck.com**  
```
;
; BIND data file for local loopback interface
;
$TTL    604800
@       IN      SOA     ns.goodluck.com. admin.goodluck.com. (
                         2024120421     ; Serial
                         604800         ; Refresh
                          86400         ; Retry
                        2419200         ; Expire
                         604800 )       ; Negative Cache TTL
;
@       IN      NS      localhost.
@       IN      A       192.168.23.62
www     IN      A       192.168.23.62
```

## 3. check on client machine  
**add "nameserver 192.168.8.52" in /etc/resolv.conf of client machine**  

**dig goodluck.com**  
```
; <<>> DiG 9.18.28-0ubuntu0.24.04.1-Ubuntu <<>> goodluck.com
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 61902
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 1232
; COOKIE: 62c10e7fbcc0a2ae0100000067505f6771e5f0d80e77c012 (good)
;; QUESTION SECTION:
;goodluck.com.                  IN      A

;; ANSWER SECTION:
goodluck.com.           604800  IN      A       192.168.23.62

;; Query time: 0 msec
;; SERVER: 192.168.23.52#53(192.168.23.52) (UDP)
;; WHEN: Wed Dec 04 21:55:58 HKT 2024
;; MSG SIZE  rcvd: 85
```

**dig www\.goodluck\.com**  
```
; <<>> DiG 9.18.28-0ubuntu0.24.04.1-Ubuntu <<>> www.goodluck.com
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 17992
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 1232
; COOKIE: 95fc1427421e63890100000067505fa1d9ec1743c9ca8865 (good)
;; QUESTION SECTION:
;www.goodluck.com.              IN      A

;; ANSWER SECTION:
www.goodluck.com.       604800  IN      A       192.168.23.62

;; Query time: 1 msec
;; SERVER: 192.168.23.52#53(192.168.23.52) (UDP)
;; WHEN: Wed Dec 04 21:56:56 HKT 2024
;; MSG SIZE  rcvd: 89
```

**ping goodluck.com**  
```
PING goodluck.com (192.168.23.62) 56(84) bytes of data.
64 bytes from 192.168.23.62: icmp_seq=1 ttl=64 time=0.018 ms
```

**ping www\.goodluck\.com**  
```
PING www.goodluck.com (192.168.23.62) 56(84) bytes of data.
64 bytes from 192.168.23.62: icmp_seq=1 ttl=64 time=0.018 m
```

## 4. Reference  
[bind9](https://www.cnblogs.com/doherasyang/p/14464999.html)  