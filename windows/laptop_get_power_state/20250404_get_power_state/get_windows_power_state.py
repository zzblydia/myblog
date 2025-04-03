import psutil

battery = psutil.sensors_battery()
if battery:
    print(f"电池剩余电量: {battery.percent}%")
    print("电池正在充电。" if battery.power_plugged else "电池未在充电。")
else:
    print("没有检测到电池。")