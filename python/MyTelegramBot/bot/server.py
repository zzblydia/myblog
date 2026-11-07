"""server 模式:长期在线,响应管理员命令并按日推送。

本模块只决定"发给谁、怎么发",查询细节全部在 business/singtel.py,
因此这里不出现签名算法、HTTP 请求等业务实现。
"""

import logging

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.schedule import register_daily_job
from business.singtel import run_singtel

log = logging.getLogger(__name__)


def build_server_app(config: dict) -> Application:
    """创建 Application 并注册唯一的消息处理入口。"""
    app = ApplicationBuilder().token(config["bot_token"]).build()
    app.bot_data["config"] = config
    # 只注册一个 handler,内部再按会话类型分派,避免同一 update 被处理两次
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    return app


def run_server(config: dict) -> None:
    """装配并启动 polling,阻塞直到进程退出。"""
    app = build_server_app(config)
    register_daily_job(app)  # 定时器不可用时在此处报错退出,而不是抛 AttributeError
    log.info("Server mode: starting polling (daily push at 06:00 SGT / 22:00 UTC)")
    app.run_polling()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """统一入口:按更新类型分派给频道/私聊/群聊处理函数。

    MessageHandler(filters.ALL) 通过 Update.effective_message 匹配,频道帖子
    (channel_post)与普通消息共用同一个 handler,所以这里必须先分流:
    否则 update.message 为 None,频道帖子会被静默丢弃。
    """
    if update.channel_post is not None:
        _log_channel_post(update)
        return

    message = update.message
    if message is None:
        return

    if message.chat.type == ChatType.PRIVATE:
        await handle_private_message(update, context)
    else:
        await handle_group_message(update, context)


def _log_channel_post(update: Update) -> None:
    """永久保留:仅打印频道 ID,用于填写 config.news_channel_id;绝不回复频道。

    前提:bot 必须是该频道的管理员,否则 Telegram 不会下发 channel_post。
    该函数是获取私有频道数字 ID(-100 开头)的唯一途径,不要删除。
    """
    post = update.channel_post
    chat = post.chat
    log.info(
        "Channel post - channel_id: %s, channel_title: %s, username: %s, "
        "message_id: %s, message: %s",
        chat.id, chat.title, chat.username, post.message_id,
        post.text or post.caption or "",
    )


async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    user = message.from_user

    log.info(
        "Private message - user_id: %s, nickname: %s, message: %s",
        getattr(user, "id", None), getattr(user, "full_name", None), message.text or "",
    )

    await _respond_admin_query(update, context)


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    user = message.from_user
    chat = message.chat

    log.info(
        "Group message - group_id: %s, group_name: %s, "
        "user_id: %s, nickname: %s, message: %s",
        chat.id, chat.title,
        getattr(user, "id", None), getattr(user, "full_name", None), message.text or "",
    )

    await _respond_admin_query(update, context)


async def _respond_admin_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """私聊/群聊共用的命令处理:仅管理员、仅 /query singtel。"""
    message = update.message
    config: dict = context.bot_data["config"]
    admin_user_id = config.get("admin_user_id", "")

    # 未配置管理员:只记录日志,任何消息都不响应
    if not admin_user_id:
        return

    user = message.from_user
    if user is None or str(user.id) != str(admin_user_id):
        return

    if (message.text or "").strip() != "/query singtel":
        return

    log.info("Received /query singtel from admin")
    # 查询与异常处理都在 business 层完成,这里只负责投递文本
    await message.reply_text(run_singtel(config))
