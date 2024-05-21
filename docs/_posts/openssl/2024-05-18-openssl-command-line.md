---
title:  "openssl-command-line"
date:   2024-05-18 02:30:00 +0800
last_modified_at: 2024-05-21 19:58:00 +0800
categories: openssl
---

# openssl command line  

1.显示证书内容  
```
openssl x509 -in libwebsockets-test-server.pem -text -noout
```

2.生成带有SAN的证书  

类型为IP:  
```
openssl req -new -newkey rsa:2048 -days 10000 -nodes -x509 -subj "/O=lws/CN=192.168.1.2" -keyout "1.key.pem" -out "1.pem" -extensions SAN -config <(echo "[req]"; echo distinguished_name=req; echo "[SAN]"; echo subjectAltName=IP:192.168.1.2)
```

类型为DNS:  
```
openssl req -new -newkey rsa:2048 -days 10000 -nodes -x509 -subj "/O=lws/CN=example.com" -keyout "1.key.pem" -out "1.pem" -extensions SAN -config <(echo "[req]"; echo distinguished_name=req; echo "[SAN]"; echo subjectAltName=DNS:example.com)
```