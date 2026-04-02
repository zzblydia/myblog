#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import time
from datetime import datetime
import psutil
from miio import Device


def setup_logger():
    """
    设置日志系统，日志文件名为启动时间戳
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"BatteryGuard 启动，日志文件：{log_filename}")
    return logger


def load_config(config_path="config.json"):
    """
    加载配置文件
    """
    logger = logging.getLogger(__name__)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 验证必需的配置项
        required_keys = ['device_ip', 'device_token', 'local_ip']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"配置文件缺少必需项：{key}")

        # 设置默认阈值
        config.setdefault('battery_low_threshold', 70)
        config.setdefault('battery_high_threshold', 90)

        logger.info("配置文件加载成功")
        logger.info(f"本机IP: {config['local_ip']}")
        logger.info(f"设备IP: {config['device_ip']}")
        logger.info(f"低电量阈值: {config['battery_low_threshold']}%")
        logger.info(f"高电量阈值: {config['battery_high_threshold']}%")

        return config

    except FileNotFoundError:
        logger.error(f"配置文件不存在：{config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"配置文件JSON格式错误：{e}")
        raise
    except Exception as e:
        logger.error(f"加载配置文件失败：{e}")
        raise


def check_local_ip(local_ip):
    """
    检查当前设备网卡列表中是否存在指定的IP地址
    :param local_ip: 要检查的IP地址
    :return: True(存在)/False(不存在)
    """
    logger = logging.getLogger(__name__)

    try:
        # 获取所有网络接口的地址信息
        net_if_addrs = psutil.net_if_addrs()

        # 遍历所有网络接口
        for interface_name, addr_list in net_if_addrs.items():
            for addr in addr_list:
                # 只检查IPv4地址
                if addr.family == 2:  # AF_INET = 2 (IPv4)
                    if addr.address == local_ip:
                        logger.debug(f"本机IP {local_ip} 存在于网卡 {interface_name}")
                        return True

        logger.warning(f"本机IP {local_ip} 不存在于当前网卡列表中")
        return False

    except Exception as e:
        logger.error(f"检查本机IP时发生错误: {e}", exc_info=True)
        return False


def get_battery_info():
    """
    获取电池信息
    :return: (percent, is_charging) 元组，percent为电量百分比，is_charging为是否正在充电
             如果获取失败返回 (None, None)
    """
    logger = logging.getLogger(__name__)

    try:
        battery = psutil.sensors_battery()

        if battery is None:
            logger.warning("未检测到电池，可能是台式机或电池未正确连接")
            return None, None

        percent = battery.percent
        is_charging = battery.power_plugged
        return percent, is_charging

    except Exception as e:
        logger.error(f"获取电池信息失败: {e}", exc_info=True)
        return None, None


def get_plug_status(device_ip, device_token):
    """
    获取插座开关状态
    :param device_ip: 插座IP地址
    :param device_token: 插座Token
    :return: True(开启)/False(关闭)/None(获取失败)
    """
    logger = logging.getLogger(__name__)

    try:
        device = Device(device_ip, device_token)

        # 使用MIoT协议查询开关状态 (siid=2, piid=1)
        result = device.send("get_properties", [{"siid": 2, "piid": 1}])

        if result and len(result) > 0:
            status = result[0].get('value')
            logger.info(f"插座当前状态: {'开启' if status else '关闭'}")
            return status
        else:
            logger.error(f"获取插座状态失败，返回结果异常: {result}")
            return None

    except Exception as e:
        logger.error(f"获取插座状态时发生错误: {e}", exc_info=True)
        return None


def control_plug(device_ip, device_token, turn_on):
    """
    控制插座开关
    :param device_ip: 插座IP地址
    :param device_token: 插座Token
    :param turn_on: True为开启，False为关闭
    :return: 操作是否成功
    """
    logger = logging.getLogger(__name__)
    action = "开启" if turn_on else "关闭"

    try:
        device = Device(device_ip, device_token)

        # 使用MIoT协议设置开关状态 (siid=2, piid=1)
        result = device.send("set_properties", [{"siid": 2, "piid": 1, "value": turn_on}])

        if result and len(result) > 0:
            code = result[0].get('code', -1)
            if code == 0:
                logger.info(f"插座{action}成功")
                return True
            else:
                logger.error(f"插座{action}失败，返回码: {code}")
                return False
        else:
            logger.error(f"插座{action}失败，返回结果异常: {result}")
            return False

    except Exception as e:
        logger.error(f"控制插座时发生错误: {e}", exc_info=True)
        return False


def main():
    """
    主函数
    """
    # 初始化日志
    logger = setup_logger()

    try:
        # 加载配置
        config = load_config()

        local_ip = config['local_ip']
        low_threshold = config['battery_low_threshold']
        high_threshold = config['battery_high_threshold']
        device_ip = config['device_ip']
        device_token = config['device_token']

        # 主循环
        logger.info("进入主循环，每60秒检查一次电池状态")

        while True:
            try:
                # 首先检查本机IP是否存在
                if not check_local_ip(local_ip):
                    logger.warning("本机IP不存在，跳过本次检查")
                    time.sleep(60)
                    continue

                # 获取电池信息
                percent, is_charging = get_battery_info()

                # 如果获取电池信息失败，跳过本次循环
                if percent is None:
                    logger.warning("无法获取电池信息，跳过本次检查")
                    time.sleep(60)
                    continue

                percent = int(percent) # 避免debian12环境下精度太高
                # 判断是否需要操作
                need_turn_on = False
                need_turn_off = False

                if percent < low_threshold and not is_charging:
                    logger.info(f"电量低于 {low_threshold}% 且未充电，需要开启插座")
                    need_turn_on = True
                elif percent > high_threshold and is_charging:
                    logger.info(f"电量高于 {high_threshold}% 且正在充电，需要关闭插座")
                    need_turn_off = True
                else:
                    logger.info(f"电池信息 - 电量: {percent}%, 充电状态: {'充电中' if is_charging else '未充电'}")

                # 控制插座
                if need_turn_on or need_turn_off:
                    # 先获取插座当前状态
                    current_status = get_plug_status(device_ip, device_token)

                    if current_status is None:
                        logger.error("无法获取插座状态，跳过本次操作")
                    else:
                        # 根据当前状态决定是否执行操作
                        if need_turn_on:
                            if current_status:
                                logger.debug("插座已经是开启状态，无需重复操作")
                            else:
                                logger.info(f"电池信息 - 电量: {percent}%, 正在打开插座")
                                control_plug(device_ip, device_token, True)
                        elif need_turn_off:
                            if not current_status:
                                logger.debug("插座已经是关闭状态，无需重复操作")
                            else:
                                logger.info(f"电池信息 - 电量: {percent}%, 正在关闭插座")
                                control_plug(device_ip, device_token, False)

                logger.debug("本次检查完成，等待下一次检查...")

            except Exception as e:
                logger.error(f"主循环中发生错误：{e}", exc_info=True)

            # 等待60秒
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("用户中断程序，正在退出...")
    except Exception as e:
        logger.critical(f"程序发生致命错误：{e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()