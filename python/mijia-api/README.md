# 笔记本电脑自动充电/断电  
项目源于笔记本电脑的电池因为长期充电鼓包了, 换了新电池后购买了`小米智能插座3`.  
希望插座能根据笔记本电脑的电量自动充电和断电.

## target  
```
1.电量低于30%, 发送消息打开插座, 充电.
2.电量高于90%, 发送消息关闭插座, 断电.
3.笔记本关机, 发送消息关闭插座, 断电.
```

## file list  
| 文件名 | 说明                                   |
| ----- |--------------------------------------|
| action_client.py | 客户端脚本, 笔记本端运行, 用于向服务端定时发送电源电量和充电状态   |
| action_server.py| 服务端脚本, 在路由器运行, 用于根据条件控制插座开启还是关闭          |
| login.py | 用于使用二维码登录mi-home,以跳过短信二次验证, 获取登录鉴权信息             |
| query.py | 用于获取设备的token信息                                                    |


## action-client.py  
<!--
windows下安装netifaces失败, 原因是:  
```
error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/

```
-->

因为在pycharm的venv里能运行, 则打开到action-client.py所在的文件夹执行:  
```
source ./.venv/Scripts/activate
pip list
pip install pyinstaller
pyinstaller.exe --version
pyinstaller.exe -F action-client.py
```
然后生成action-client.exe可以在windows环境下运行, 并设置任务计划在系统启动时执行.  

## action-server.py  
```
pip install python-miio # 便于使用命令miiocli, 实现根据局域网ip和token控制设备. 依赖于python3 python3-pip python3-dev gcc

nohup python3 -u action-server.py >/dev/null & # -u 用于日志立即写入run.log
```

## new way  
1.一般来讲, 笔记本使用客户端脚本根据电量和充电状态, 直接向小米插座发送开关命令即可.  
2.之所以还有一个服务端脚本, 是想着笔记本关机之后能关闭插座, 这样才能避免电池长期重启. 但是1实现不了.  
今天发现一个新思路就是利用`小米智能插座3`的自动化, 条件设置为`功率低于30W`的时候自动关闭插座.  