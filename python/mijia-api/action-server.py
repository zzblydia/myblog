import socket
import json
import subprocess
import logging
from datetime import datetime, timedelta

SERVER_IP = "192.168.8.62"
SERVER_PORT = 58000
BATTERY_PERCENT_MIN = 50  # 低于百分比则开始充电
BATTERY_PERCENT_MAX = 90  # 高于百分比则停止充电
DEVICE_IP = "192.168.8.93"
DEVICE_DID = "aaa"
DEVICE_TOKEN = "bbb"

# Shell command template as a global constant
SHELL_COMMAND_TEMPLATE = (
    "miiocli device --ip {device_ip} --token {device_token} raw_command set_properties "
    '"[{{\'did\': \'{device_did}\', \'siid\': 2, \'piid\': 1, \'value\':{value}}}]"'
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 设置默认日志级别为 INFO
    format='[%(asctime)s - %(levelname)s] %(message)s',  # 时间戳 - 级别 - 消息
    handlers=[
        logging.FileHandler('run.log', mode='a'),  # 追加到 run.log
        # logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)

class TCPServer:
    def __init__(self):
        self.ip = SERVER_IP
        self.port = SERVER_PORT
        self.device_ip = DEVICE_IP
        self.device_did = DEVICE_DID
        self.device_token = DEVICE_TOKEN
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.settimeout(3)  # 3 seconds timeout
        self.last_valid_data_time = datetime.now()  # Initialize to start time
        self.current_state = False  # Initialize state to False (off)

    def set_switch_off(self):
        shell_command = SHELL_COMMAND_TEMPLATE.format(
            device_ip=self.device_ip,
            device_did=self.device_did,
            device_token=self.device_token,
            value="False"
        )
        try:
            result = subprocess.run(
                shell_command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"set_switch_off executed successfully response: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing set_switch_off: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error executing set_switch_off: {str(e)}")
        self.current_state = False

    def set_switch_on(self):
        shell_command = SHELL_COMMAND_TEMPLATE.format(
            device_ip=self.device_ip,
            device_did=self.device_did,
            device_token=self.device_token,
            value="True"
        )
        try:
            result = subprocess.run(
                shell_command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"set_switch_on executed successfully: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing set_switch_on: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error executing set_switch_on: {str(e)}")
        self.current_state = True

    def start(self):
        try:
            self.server_socket.bind((self.ip, self.port))
            self.server_socket.listen(1)
            self.current_state = True  # 启动后默认认为插座是打开状态
            logger.info(f"Server listening on {self.ip}:{self.port}")

            while True:
                try:
                    client_socket, addr = self.server_socket.accept()
                    data = client_socket.recv(1024).decode('utf-8')

                    if data:
                        current_time = datetime.now()
                        logger.info(f"Received data at {current_time}: {data}")

                        try:
                            json_data = json.loads(data)
                            percent = json_data.get('BatteryPercentage')
                            is_charging = json_data.get('IsCharging')

                            if percent < BATTERY_PERCENT_MIN and not is_charging:
                                self.set_switch_on()
                            elif percent > BATTERY_PERCENT_MAX and is_charging:
                                self.set_switch_off()

                            # 如果数据有效则更新数据接收时间
                            self.last_valid_data_time = current_time

                        except json.JSONDecodeError:
                            logger.warning("Invalid JSON, continuing to listen...")
                            continue

                    client_socket.close()
                except socket.timeout:
                    # Timeout occurred, check for 3-minute timeout if state is on
                    if self.current_state:
                        time_diff = datetime.now() - self.last_valid_data_time
                        # if time_diff > timedelta(seconds=5):
                        if time_diff > timedelta(minutes=3):
                            self.set_switch_off()
                            self.last_valid_data_time = datetime.now()  # Reset to current time

        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.server_socket.close()

if __name__ == "__main__":
    server = TCPServer()
    server.start()