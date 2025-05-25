---
title:  "Python for Xiaomi Smart Socket"
date:   2025-04-25 00:08:00 +0800
last_modified_at: 2025-04-29 06:45:00 +0800
categories: python
tags: xiaomi-switch
published: false
---

# Python for Xiaomi Smart Socket  
My laptop battery is swollen because of long-time charging.  
After I bought a new one, I decided to find out how to auto-charge using the Xiaomi Smart Socket 3.  
My target is as follows:  

```
1. When the battery percentage is below 50%, it starts charging.
2. When the battery percentage exceeds 90%, it stops charging.
3. When the laptop is shut down, it stops charging.
```

## 过程  
以下两种方式都获取失败, 原因是遇到账号需要短信二次验证..  

1>miiocli cloud  
[python-miio](https://github.com/rytilahti/python-miio)  

2>token_extractor.py  
[Home Assistant](https://www.home-assistant.io/integrations/xiaomi_miio#retrieving-the-access-token)  

## 转机  
[通过python控制米家中的智能设备](https://blog.ulna520.top/2024/09/19/mijia/)  
[mijia-api](https://github.com/Do1e/mijia-api)  

## commands  
siid, 可以理解为方法id  
piid, 可以理解为参数id  

[米家智能插座3 actions和parameters](https://home.miot-spec.com/spec/cuco.plug.v3)  

```
查询固件版本等信息
miiocli device --ip IP --token abcde info  

开
miiocli -d device --ip IP --token abcde raw_command set_properties "[{'did': 'MYDID', 'siid': 2, 'piid': 1, 'value':True}]"


关
miiocli -d device --ip IP --token abcde raw_command set_properties "[{'did': 'MYDID', 'siid': 2, 'piid': 1, 'value':False}]"

获取开关状态
miiocli -d device --ip IP --token abcde raw_command get_properties "[{'did': 'MYDID', 'siid': 2, 'piid': 1}]"
```


## reference  
[通过API获取小米WIFI插座属性来实现自动化](https://www.fxxkcar.com/blog/?p=323)  
