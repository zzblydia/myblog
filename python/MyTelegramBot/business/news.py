"""每日 60 秒读懂世界新闻(60s API)。

只负责"拿到要发送的内容":不 import telegram、不知道 chat_id、不发送消息。
发送动作由 bot/client.py 完成。
"""

import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

# 调试链接:仅用于本地测试接口,不参与生产请求;需要调试时临时把 NEWS_URL 指过来
DEBUG_NEWS_URL = "https://60s.viki.moe/v2/60s"

# 生产链接:主用失败自动切备用
NEWS_URL = "https://60s.okbaike.com/v2/60s"
NEWS_BACKUP_URL = "https://60s.zellon.top/v2/60s"

_REQUEST_TIMEOUT = 15

_TAG_RE = re.compile(r"<[^>]+>")   # 仅用于长度估算,正文里不会出现用户提供的标签


@dataclass(frozen=True)
class DailyNews:
    """当日新闻的原始字段;文本排版由 format_news_message 负责。"""

    date: str            # API 原样,如 "2026-11-01"
    day_of_week: str     # 如 "星期日"
    lunar_date: str      # 如 "丙午年九月廿三"
    news: list[str]      # 新闻条目,保持 API 顺序
    tip: str             # 微语
    link: str            # 原文链接
    image: str           # 当日海报直链,可能为空


def fetch_daily_news() -> DailyNews | None:
    """拉取当日新闻;任何异常记录日志后返回 None。

    调用方据此决定"不发频道",避免把错误提示当成新闻发出去。
    """
    try:
        return _fetch()
    except Exception as exc:  # 网络、解析、业务码异常统一在此收口
        logger.exception("Daily news fetch failed: %s", exc)
        return None


def format_news_message(news: DailyNews, channel_title: str = "") -> str:
    """拼装待发送的 HTML 文本(配合 Telegram parse_mode=HTML)。

    频道标题由 bot 层通过 get_chat 取得后传入:业务层不接触 telegram 对象。
    Telegram 不支持文字颜色,这里用 emoji + 加粗做视觉强调;
    所有动态内容统一转义,避免新闻里的 & < > 触发 "can't parse entities"。
    原文链接(data.link)按需求不展示,但字段仍保留在 DailyNews 中。
    """
    lines: list[str] = []

    # 频道标题放第一行,便于读者先确认来源
    if channel_title:
        lines.append(f"📢 <b>{_escape(channel_title)}</b>")

    # 日期按中文习惯去掉前导零:2026-11-01 -> 2026年11月1日
    date_text = _format_date(news.date)
    header = " ".join(part for part in (date_text, news.day_of_week) if part)
    if header:
        lines.append(f"📅 <b>{_escape(header)}</b>")
    if news.lunar_date:
        lines.append(f"🌙 农历 {_escape(news.lunar_date)}")
    if lines:
        lines.append("")

    # 每条新闻之间空一行,提升可读性
    items = [
        f"{index}. {_escape(item)}"
        for index, item in enumerate(news.news, start=1)
    ]
    lines.append("\n\n".join(items))

    if news.tip:
        lines.extend(["", f"【微语】{_escape(news.tip)}"])

    return "\n".join(lines)


def _escape(text: str) -> str:
    """HTML 转义;quote=False 只处理 & < >,避免正文被无谓拉长。"""
    return html.escape(str(text), quote=False)


def plain_text_length(text: str) -> int:
    """返回 Telegram 口径的正文长度(UTF-16 码元,不含 HTML 标签与实体)。

    Telegram 的 1024 图注上限按 "entities 解析后" 的文本计算,emoji 在 UTF-16
    中占 2 个码元,所以不能直接用 len() 判断能否塞进图注。
    """
    plain = html.unescape(_TAG_RE.sub("", text))
    return len(plain.encode("utf-16-le")) // 2


def download_news_image(url: str) -> bytes | None:
    """下载海报字节,供 Telegram 拉不到直链时兜底上传;失败返回 None。"""
    if not url:
        return None

    try:
        response = requests.get(url, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.content
    except Exception as exc:
        logger.warning("News image download failed: %s", exc)
        return None


def get_news_image_url(news: DailyNews) -> str:
    """预留的配图接口:返回本次要发送的图片直链,空串表示不发图。

    当前 60s 海报内容与文字正文完全重复,所以先返回空串;
    后续改用其他图源时只改这里(调用别的接口、按日期拼 URL 等),
    bot/client.py 的发送逻辑无需改动。
    """
    return ""


def _fetch() -> DailyNews:
    """按「主用 → 备用」顺序请求,任一成功即返回;全部失败时抛出最后一个异常。"""
    last_exc: Exception | None = None
    for url in (NEWS_URL, NEWS_BACKUP_URL):
        try:
            return _fetch_from(url)
        except Exception as exc:  # 单个地址失败不影响切换下一个
            last_exc = exc
            logger.warning("News fetch from %s failed: %s", url, exc)

    # 两个地址都不可用:交给 fetch_daily_news 统一记录并返回 None
    raise last_exc if last_exc is not None else RuntimeError("No news URL configured")


def _fetch_from(url: str) -> DailyNews:
    """向单个地址发起请求并解析;任何异常向上抛出,由 _fetch 决定是否切换。"""
    response = requests.get(
        url,
        params={"encoding": "json"},   # json 才能校验业务码与空列表
        timeout=_REQUEST_TIMEOUT,
    )

    logger.debug("News response status: %s (%s)", response.status_code, url)
    response.raise_for_status()

    payload = response.json()
    # 注意:本接口成功码是 200,不是 singtel 接口的 1
    if payload.get("code") != 200:
        raise ValueError(
            f"API error {payload.get('code')}: {payload.get('message', 'unknown error')}"
        )

    data = payload.get("data") or {}
    news = data.get("news") or []
    if not news:
        raise ValueError("API returned empty news list")

    image = data.get("image") or ""
    if not image:
        # 缺图不致命:客户端会跳过图片只发文字
        logger.warning("News image URL missing, will send text only")

    return DailyNews(
        date=data.get("date") or "",
        day_of_week=data.get("day_of_week") or "",
        lunar_date=data.get("lunar_date") or "",
        news=[str(item) for item in news],
        tip=data.get("tip") or "",
        link=data.get("link") or "",
        image=image,
    )


def _format_date(raw: str) -> str:
    """把 2026-11-01 转成 2026年11月1日;解析失败时原样返回。"""
    try:
        parsed = datetime.strptime(raw, "%Y-%m-%d")
    except (TypeError, ValueError):
        return raw
    return f"{parsed.year}年{parsed.month}月{parsed.day}日"


if __name__ == "__main__":
    # 单文件调试入口:仅本文件直接运行时生效,不影响 main.py 的初始化流程
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    daily = fetch_daily_news()
    print(format_news_message(daily, "调试频道") if daily else "新闻获取失败")
