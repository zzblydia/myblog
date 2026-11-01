"""client 模式:由外部定时器(如 GitHub Actions)触发,查询一次后退出。"""

import logging

from telegram import Bot

from business.singtel import query_singtel_data

log = logging.getLogger(__name__)


async def run_client(config: dict) -> None:
    admin_user_id = config.get("admin_user_id", "")
    if not admin_user_id:
        log.error("client mode: admin_user_id 未配置,无法发送消息")
        return

    # client 模式不需要 Application/job_queue,直接用 Bot 发一条消息即可
    async with Bot(token=config["bot_token"]) as bot:
        await bot.send_message(
            chat_id=admin_user_id,
            text=query_singtel_data(config.get("order_id", "")),
        )

    log.info("Client mode finished")
