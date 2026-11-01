"""client 模式:由外部定时器(如 GitHub Actions)触发,执行一次后退出。

任务由 config.client_task 决定:
- singtel:查询套餐余量并推送给管理员;
- news:拉取每日新闻并发布到频道(正文可放进图注时合并为一条,否则图片 + 文字)。
"""

import logging
import re

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from business.news import (
    download_news_image,
    fetch_daily_news,
    format_news_message,
    get_news_image_url,
    plain_text_length,
)
from business.singtel import query_singtel_data

log = logging.getLogger(__name__)

_SPLIT_LIMIT = 4000      # Telegram 单条上限 4096,留余量避免分片后仍超限
_CAPTION_LIMIT = 1000    # 图注上限 1024,按解析后长度判断,留少量余量
_PUBLIC_CHANNEL_PREFIXES = ("https://t.me/", "http://t.me/", "t.me/")


async def run_client(config: dict, task: str) -> int:
    """执行一次任务并返回进程退出码(0 成功,非 0 失败)。"""
    if task == "news":
        return await _run_news(config)
    return await _run_singtel(config)


async def _run_singtel(config: dict) -> int:
    """原 client 行为:查询一次套餐余量并发给管理员。

    order_id 与 admin_user_id 已在 main._validate_config 中校验,这里直接使用。
    Telegram 侧失败统一在此收口,避免 traceback 冒到 main。
    """
    # client 模式不需要 Application/job_queue,直接用 Bot 发一条消息即可
    try:
        async with Bot(token=config["bot_token"]) as bot:
            await bot.send_message(
                chat_id=config["admin_user_id"],
                text=query_singtel_data(config.get("order_id", "")),
            )
    except TelegramError as exc:
        log.error("Singtel query failed: %s", exc)
        return 1

    log.info("Client mode finished: singtel")
    return 0


async def _run_news(config: dict) -> int:
    """拉取新闻并发布到频道;获取失败时退出码 1,便于 Actions 报警。"""
    channel_id = _normalize_channel_id(str(config.get("news_channel_id") or ""))
    if channel_id is None:
        log.error("client mode: news_channel_id 缺失或无法解析,无法发布新闻")
        return 1

    news = fetch_daily_news()
    if news is None:
        log.error("client mode: 新闻获取失败,本次不发布")
        return 1

    # Telegram 侧失败统一在此收口(含 Bot 初始化、get_chat、send),避免 traceback
    try:
        async with Bot(token=config["bot_token"]) as bot:
            channel_title = await _get_channel_title(bot, channel_id)
            text = format_news_message(news, channel_title)

            # 图源由 business.get_news_image_url 决定;返回空串时不发图,只发文字
            image_url = get_news_image_url(news)
            caption = text if image_url and plain_text_length(text) <= _CAPTION_LIMIT else None
            photo_sent = await _send_photo(bot, channel_id, image_url, caption=caption)

            # 图注已带完整正文时不再重复发送;图片缺失/发送失败/正文超长时单独发文字
            if caption is None or not photo_sent:
                for chunk in _split_text(text, _SPLIT_LIMIT):
                    await bot.send_message(
                        chat_id=channel_id,
                        text=chunk,
                        parse_mode=ParseMode.HTML,
                    )
    except TelegramError as exc:
        log.error("News push failed: %s", exc)
        return 1

    log.info("Client mode finished: news, channel=%s", channel_id)
    return 0


async def _get_channel_title(bot: Bot, channel_id: str) -> str:
    """取频道标题用于正文头部;失败不影响发送,返回空串。"""
    try:
        chat = await bot.get_chat(channel_id)
        return chat.title or ""
    except TelegramError as exc:
        log.warning("Failed to get channel title for %s: %s", channel_id, exc)
        return ""


async def _send_photo(
    bot: Bot,
    channel_id: str,
    image_url: str,
    caption: str | None = None,
) -> bool:
    """先让 Telegram 自己按 URL 拉图,失败再下载后上传;返回是否发送成功。

    图片是附加信息,任何失败都不应阻断新闻正文投递,所以只返回状态不抛异常。
    caption 为 None 时发送无图注的图片。
    """
    if not image_url:
        # 当前图源默认返回空串,属于预期行为,不产生告警日志
        log.debug("No image URL, sending text only")
        return False

    try:
        await bot.send_photo(
            chat_id=channel_id,
            photo=image_url,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
        return True
    except TelegramError as exc:
        log.warning("send_photo by URL failed (%s), retrying with downloaded bytes", exc)

    content = download_news_image(image_url)
    if content is None:
        log.warning("News image unavailable, sending text only")
        return False

    try:
        await bot.send_photo(
            chat_id=channel_id,
            photo=content,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
        return True
    except TelegramError as exc:
        log.warning("send_photo with bytes failed, sending text only: %s", exc)
        return False


def _normalize_channel_id(raw: str) -> str | None:
    """把常见写法统一成 Bot API 可接受的形式。

    - @name / name / t.me/name / https://t.me/name -> @name
    - -100xxx 数字 ID -> 原样
    - t.me/+邀请链接 -> None(邀请链接无法被 Bot API 解析)
    """
    value = raw.strip()
    if not value:
        return None

    # 频道/群组数字 ID:可带一个前导负号,后面必须是纯数字
    if re.fullmatch(r"-?\d+", value):
        return value

    if value.startswith("@"):
        return value

    for prefix in _PUBLIC_CHANNEL_PREFIXES:
        if value.startswith(prefix):
            value = value[len(prefix):]
            break

    # 邀请链接(+xxxx)与带路径的链接都无法解析
    if not value or value.startswith("+") or "/" in value:
        log.error(
            "news_channel_id 无法解析: %s;请使用 @username 或 -100 开头的数字 ID",
            raw,
        )
        return None

    return f"@{value}"


def _split_text(text: str, limit: int) -> list[str]:
    """按行切分文本,保证每片不超过 limit;单行超长时硬切。"""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in text.splitlines():
        # 单行本身就超限:先冲掉已积累内容,再硬切该行
        while len(line) > limit:
            if current:
                chunks.append("\n".join(current))
                current, current_len = [], 0
            chunks.append(line[:limit])
            line = line[limit:]

        line_len = len(line) + (1 if current else 0)   # 计入与上一行之间的换行符
        if current_len + line_len > limit:
            chunks.append("\n".join(current))
            current, current_len = [line], len(line)
        else:
            current.append(line)
            current_len += line_len

    if current:
        chunks.append("\n".join(current))

    # 空文本返回空列表,调用方 for 循环自然跳过,不会发空消息
    return chunks
