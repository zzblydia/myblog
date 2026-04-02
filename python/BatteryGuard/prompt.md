# BatteryGuard.py  
我正在使用python3.11.2.实现一个脚本, 运行在windows或者linux上.  
脚本的主要功能是循环获取设备的充电状态和电池电量, 并根据剩余电量决定开启插座或者关闭插座.
插座的型号是`小米智能插座3`, model类型为`cuco.plug.v3`.

## 实现逻辑
1.脚本能单独调测.
2.脚本启动后初始化日志,在当前目录下生成log文件, 文件名为启动的时间戳, 日志级别默认为info级别.
3.脚本启动后读取config.json,读取local_ip, device_ip, device_token,battery_low_threshold,battery_high_threshold
4.脚本进入循环, 每1分钟执行一次.
5.首先检查当前设备网卡列表里是否存在local_ip,如果不存在则进入下次循环.
6.通过psutil实现函数GetBatteryInfo获取电池剩余电量和充电状态
7.如果剩余电量小于阈值且没有充电 或者剩余电量高于阈值且在充电, 则去获取智能插座的开关状态, 并对应执行打开或关闭操作.
8.我已经通过mijiaAPI获取了局域网中小米插座的device_ip和device_token.
9.我希望获取开关状态和操作开关都使用局域网通信, 不依赖于互联网.可以考虑使用python-miio,如果有更好的方案则优先使用.


接下来我们一步一步实现这个脚本, 在我们探讨清楚方案前请勿编写代码, 你有疑问可以现在让我补充.
