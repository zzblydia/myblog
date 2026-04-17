import asyncio
import logging
from datetime import time, timezone

from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot_config import load_config
from bot_logger import init_logging
from query_mobile_data import query_singtel_data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_message(update: Update) -> None:
    """Log incoming message details."""
    message = update.message
    if not message:
        return

    user = message.from_user
    chat = message.chat
    text = message.text or ""
    log  = logging.getLogger(__name__)

    if chat.type == "private":
        log.info(
            "Private message - user_id: %s, nickname: %s, message: %s",
            user.id, user.full_name, text,
        )
    else:
        log.info(
            "Group message - group_id: %s, group_name: %s, "
            "user_id: %s, nickname: %s, message: %s",
            chat.id, chat.title, user.id, user.full_name, text,
        )


async def _send_query_result(send_fn, order_id: str) -> None:
    """Run the data query and deliver the result via send_fn(text)."""
    log = logging.getLogger(__name__)
    try:
        result_msg = query_singtel_data(order_id)
        log.info("Query succeeded, sending result")
    except Exception as exc:
        log.error("Query failed: %s", exc)
        result_msg = f"查询失败: {exc}"
    await send_fn(result_msg)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log every message; respond to admin /query singtel command."""
    _log_message(update)

    message = update.message
    if not message:
        return

    config: dict = context.bot_data["config"]
    admin_user_id = config.get("admin_user_id", "")

    # No admin configured — only log, never respond
    if not admin_user_id:
        return

    # Only respond to the admin
    if str(message.from_user.id) != str(admin_user_id):
        return

    # Only respond to exactly "/query singtel"
    text = (message.text or "").strip()
    if text != "/query singtel":
        return

    log = logging.getLogger(__name__)
    log.info("Received /query singtel from admin")

    async def _reply(msg: str) -> None:
        await message.reply_text(msg)

    await _send_query_result(_reply, config.get("order_id", ""))


# ---------------------------------------------------------------------------
# Scheduled job (server mode)
# ---------------------------------------------------------------------------

async def scheduled_query(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Daily scheduled job: query and push result to admin."""
    log = logging.getLogger(__name__)
    config: dict = context.bot_data["config"]
    admin_user_id = config.get("admin_user_id", "")

    if not admin_user_id:
        log.warning("Scheduled query skipped: admin_user_id not set")
        return

    log.info("Running scheduled daily query")

    async def _send(msg: str) -> None:
        await context.bot.send_message(chat_id=admin_user_id, text=msg)

    await _send_query_result(_send, config.get("order_id", ""))


# ---------------------------------------------------------------------------
# Client (one-shot) mode
# ---------------------------------------------------------------------------

async def run_client(config: dict) -> None:
    """Query once, send to admin, then exit."""
    log = logging.getLogger(__name__)
    log.info("Running in client (one-shot) mode")

    admin_user_id = config.get("admin_user_id", "")
    if not admin_user_id:
        log.error("client mode: admin_user_id not set, cannot send message")
        return

    async with Bot(token=config["bot_token"]) as bot:
        async def _send(msg: str) -> None:
            await bot.send_message(chat_id=admin_user_id, text=msg)

        await _send_query_result(_send, config.get("order_id", ""))

    log.info("Client mode finished")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    log = init_logging()
    log.info("Bot starting")

    config = load_config()
    log.info("Config loaded, run_mode=%s", config.get("run_mode"))

    run_mode = config.get("run_mode", "server")

    if run_mode == "client":
        asyncio.run(run_client(config))
        return

    # --- server mode ---
    app = ApplicationBuilder().token(config["bot_token"]).build()
    app.bot_data["config"] = config

    app.add_handler(MessageHandler(filters.ALL, handle_message))

    # Daily scheduled push at 06:00 SGT (22:00 UTC)
    app.job_queue.run_daily(
        scheduled_query,
        time=time(hour=22, minute=0, second=0, tzinfo=timezone.utc),
        name="daily_query",
    )

    log.info("Server mode: starting polling (daily push at 06:00 SGT / 22:00 UTC)")
    app.run_polling()


if __name__ == "__main__":
    main()
