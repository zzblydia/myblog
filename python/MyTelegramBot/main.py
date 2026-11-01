"""程序入口。

只做三件事:
1. 初始化日志(必须先于配置加载,配置相关的告警才能落盘);
2. 读取并校验配置;
3. 按 config.json 中的 run_mode 分派到 client 或 server 模式。

telegram 交互在 bot/ 包,查询逻辑在 business/ 包,本文件不含具体业务代码。
"""

import asyncio
import logging

from bot.client import run_client
from bot.server import run_server
from init.config import load_config
from init.logger import init_logging

# config.example.json 里的占位前缀;命中说明用户复制了模板但没改 token
_PLACEHOLDER_TOKEN_PREFIX = "REPLACE_WITH"

# client 模式下 config.client_task 的合法取值
_CLIENT_TASKS = ("singtel", "news")
_DEFAULT_CLIENT_TASK = "singtel"   # 缺省值保持老配置、老 workflow 的行为不变


def _validate_config(config: dict, log: logging.Logger) -> None:
    """校验启动必需项,失败时给出可直接执行的修复提示。"""
    token = str(config.get("bot_token") or "").strip()
    if not token or token.startswith(_PLACEHOLDER_TOKEN_PREFIX):
        log.error(
            "bot_token 未配置或仍为占位值,请编辑 config/config.json "
            "(可参考 config/config.example.json)"
        )
        raise SystemExit(1)

    # 任务只在 client 模式下有意义,server 模式忽略 client_task
    if config.get("run_mode", "server") != "client":
        return

    task = config.get("client_task", _DEFAULT_CLIENT_TASK)
    if task not in _CLIENT_TASKS:
        log.error("client_task 非法: %s(仅支持 singtel / news)", task)
        raise SystemExit(1)

    if task == "news" and not str(config.get("news_channel_id") or "").strip():
        log.error("client_task=news 但 news_channel_id 未配置,无法发布新闻")
        raise SystemExit(1)

    if task == "singtel":
        if not str(config.get("order_id") or "").strip():
            log.error("client_task=singtel 但 order_id 未配置,无法查询套餐余量")
            raise SystemExit(1)
        if not str(config.get("admin_user_id") or "").strip():
            log.error("client_task=singtel 但 admin_user_id 未配置,无法发送消息")
            raise SystemExit(1)


def _bootstrap() -> tuple[logging.Logger, dict]:
    """框架级初始化:日志 + 配置。全项目唯一允许调用这两者的位置。"""
    log = init_logging()
    config = load_config()  # 日志已就绪,配置相关的 INFO/WARNING 可正常落盘
    log.info("Config loaded, run_mode=%s", config.get("run_mode", "server"))
    _validate_config(config, log)
    return log, config


def main() -> None:
    log, config = _bootstrap()

    run_mode = config.get("run_mode", "server")
    if run_mode == "client":
        task = config.get("client_task", _DEFAULT_CLIENT_TASK)
        log.info("Client task: %s", task)
        # 退出码透传给调用方:news 任务失败时让 GitHub Actions 变红
        exit_code = asyncio.run(run_client(config, task))
        if exit_code:
            raise SystemExit(exit_code)
    elif run_mode == "server":
        run_server(config)
    else:
        log.error("未知的 run_mode: %s(仅支持 client / server)", run_mode)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
