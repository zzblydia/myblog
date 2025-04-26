import socket
import time
import json
import psutil
import logging

# 配置变量
CLIENT_IP = "192.168.8.60"  # 用于检查有没有处于局域网
SERVER_IP = "192.168.8.62"
SERVER_PORT = 58000
INTERVAL = 180  # 发送间隔，单位秒

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 设置默认日志级别为 INFO
    format='[%(asctime)s][%(levelname)s] %(message)s',  # 时间戳 - 级别 - 消息
    handlers=[
        # 不加绝对路径时, windows任务计划调用程序后生成的日志在C:\Windows\System32目录下.
        logging.FileHandler('C:\\vm\python\\run.log', mode='a'),  # 追加到 run.log
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)

def check_local_ip():
    """检查本机是否绑定了指定IP"""
    # 获取所有网络接口及其状态
    all_interfaces = psutil.net_if_stats()
    # 列表推导式（list comprehension）, 没用过...
    active_interfaces = [iface for iface, stats in all_interfaces.items() if stats.isup]

    # 遍历活跃接口
    for interface in active_interfaces:
        # 获取接口的地址信息
        addrs = psutil.net_if_addrs().get(interface, [])
        for addr in addrs:
            # 检查 IPv4 地址
            if addr.family == socket.AF_INET and addr.address == CLIENT_IP:
                return True
    return False

def get_battery_info():
    """获取电池电量和充电状态"""
    battery = psutil.sensors_battery()
    if battery is None:
        return 0, False
    return battery.percent, battery.power_plugged

def create_json_data():
    timestamp = int(time.time())
    battery_percent, is_charging = get_battery_info()
    # 客户端需要不断发送心跳消息
    # 如果仅充电状态有变化才发送, 服务端无法判断客户端是否关机
    data = {
        "time": timestamp,
        "BatteryPercentage": battery_percent,
        "IsCharging": is_charging
    }
    return json.dumps(data)

def send_tcp_request():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.settimeout(5)  # 设置连接超时
            client.bind((CLIENT_IP, 0))  # 指定客户端端口或设置端口0随机分配
            client.connect((SERVER_IP, SERVER_PORT))
            json_data = create_json_data()
            client.sendall(json_data.encode('utf-8'))
            logger.info(f"Sent data: {json_data}")
    except Exception as e:
        logger.info(f"Error sending TCP request: {e}")

def main():
    # 主循环
    while True:
        # 检查本地IP,如果不在这个网段
        if not check_local_ip():
            logger.warning(f"Local IP {CLIENT_IP} not found. rechecking.")
        else:
            send_tcp_request()
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()