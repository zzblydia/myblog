---
title:  "Python for Xiaomi Smart Socket"
date:   2025-04-25 00:08:00 +0800
last_modified_at: 2025-04-25 02:20:00 +0800
categories: python
tags: xiaomi-switch
published: false
---

# Python for Xiaomi Smart Socket  

## background  
笔记本的电池因为长期充电鼓包了, 新购了小米智能插座3,希望使用python控制小米插座, 实现以下目标:  
```
1.启动后监听ip和port
2.收到消息, 未充电且电量低于30%, 若开关关闭, 则发送消息打开开关
3.收到消息, 在充电且电量大于90%, 若开关打开, 则发送消息关闭开关
4.60秒未收到消息, 若开关打开, 则发送消息关闭开关
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
