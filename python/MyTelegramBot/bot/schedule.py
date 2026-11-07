"""server 模式的定时任务。

单独成文件的原因:全项目只有这里依赖 Application.job_queue,
"未安装 APScheduler" 的处理也集中在此处。
"""

import logging
from datetime import time, timezone

from telegram.ext import Application, ContextTypes

from business.singtel import run_singtel

log = logging.getLogger(__name__)

# 06:00 SGT (UTC+8) == 22:00 UTC;需要改推送时间只改这一行
DAILY_PUSH_TIME = time(hour=22, minute=0, second=0, tzinfo=timezone.utc)


def register_daily_job(app: Application) -> None:
    """注册每日查询任务;job_queue 缺失时给出明确提示。"""
    if app.job_queue is None:
        # PTB 在未安装 job-queue 额外依赖时会把 job_queue 静默置为 None
        log.error('job-queue 不可用:请执行 pip install "python-telegram-bot[job-queue]"')
        raise SystemExit(1)

    app.job_queue.run_daily(scheduled_query, time=DAILY_PUSH_TIME, name="daily_query")
    log.info("Daily query scheduled at 22:00 UTC (06:00 SGT)")


async def scheduled_query(context: ContextTypes.DEFAULT_TYPE) -> None:
    """每日任务:查询一次并推送给管理员。"""
    config: dict = context.bot_data["config"]
    admin_user_id = config.get("admin_user_id", "")

    if not admin_user_id:
        log.warning("Scheduled query skipped: admin_user_id not set")
        return

    log.info("Running scheduled daily query")
    await context.bot.send_message(
        chat_id=admin_user_id,
        text=run_singtel(config),
    )
