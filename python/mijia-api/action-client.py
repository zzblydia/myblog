import socket
import time
import json
import psutil
import netifaces
import logging
import sys

# 配置变量
LOCAL_IP = "192.168.8.60"
SERVER_IP = "192.168.8.62"
SERVER_PORT = 58000
INTERVAL = 60  # 发送间隔，单位秒

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 设置默认日志级别为 INFO
    format='[%(asctime)s - %(levelname)s] %(message)s',  # 时间戳 - 级别 - 消息
    handlers=[
        logging.FileHandler('run.log', mode='a'),  # 追加到 run.log
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)

def check_local_ip():
    """检查本机是否绑定了指定IP"""
    try:
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    if addr['addr'] == LOCAL_IP:
                        return True
        return False
    except Exception as e:
        logger.info(f"Error checking IP: {e}")
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
            client.connect((SERVER_IP, SERVER_PORT))
            json_data = create_json_data()
            client.sendall(json_data.encode('utf-8'))
            logger.info(f"Sent data: {json_data}")
    except Exception as e:
        logger.info(f"Error sending TCP request: {e}")


def main():
    # 检查本地IP
    if not check_local_ip():
        logger.info(f"Local IP {LOCAL_IP} not found. Exiting.")
        sys.exit(1)

    logger.info(f"Local IP {LOCAL_IP} found. Starting TCP client.")

    # 主循环
    while True:
        send_tcp_request()
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()