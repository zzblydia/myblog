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


def _validate_config(config: dict, log: logging.Logger) -> None:
    """校验启动必需项,失败时给出可直接执行的修复提示。"""
    token = str(config.get("bot_token") or "").strip()
    if not token or token.startswith(_PLACEHOLDER_TOKEN_PREFIX):
        log.error(
            "bot_token 未配置或仍为占位值,请编辑 config/config.json "
            "(可参考 config/config.example.json)"
        )
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
        asyncio.run(run_client(config))
    elif run_mode == "server":
        run_server(config)
    else:
        log.error("未知的 run_mode: %s(仅支持 client / server)", run_mode)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
