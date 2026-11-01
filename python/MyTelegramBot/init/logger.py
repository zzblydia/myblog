"""日志初始化:同时输出到按天轮转的文件和控制台。"""

import logging
import re
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# init/ 的上两级即项目根;日志统一写到 <项目根>/logs/
_PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = _PROJECT_ROOT / "logs"

_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_LOG_FILE = "bot.log"     # 当前日志固定名,便于 tail -f / 生产排查
_LOG_BACKUP_DAYS = 14     # 保留 14 份历史(约两周),超出由 handler 自动删除


class _RedactingFormatter(logging.Formatter):
    """格式化后脱敏,防止 bot token 落盘或出现在控制台。

    Telegram Bot API 的 URL 形如 https://api.telegram.org/bot<id>:<token>/method,
    httpx 在 INFO 级别就会把它打印出来(例如 getUpdates),日志一旦被分享
    就等于泄露 token,所以在写文件/输出前统一替换。
    """

    _TOKEN_RE = re.compile(r"bot\d+:[A-Za-z0-9_-]+")

    def format(self, record: logging.LogRecord) -> str:
        return self._TOKEN_RE.sub("bot<redacted>", super().format(record))


def _build_file_handler() -> logging.Handler:
    """按天轮转的文件 handler:当天写 bot.log,隔天变 bot.log.YYYYMMDD。"""
    handler = TimedRotatingFileHandler(
        LOG_DIR / _LOG_FILE,
        when="midnight",        # 机器本地时间 00:00 切分(下次写日志时执行)
        backupCount=_LOG_BACKUP_DAYS,
        encoding="utf-8",
    )
    handler.suffix = "%Y%m%d"   # 备份名形如 bot.log.20261031
    return handler


def init_logging(level: int = logging.INFO) -> logging.Logger:
    """初始化日志,返回 root logger。

    输出目标: <项目根>/logs/bot.log 与控制台(stderr)。
    文件按天轮转并保留 _LOG_BACKUP_DAYS 份;两个目标共用脱敏 formatter。
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = _RedactingFormatter(_LOG_FORMAT)

    file_handler = _build_file_handler()
    file_handler.setFormatter(formatter)

    # 默认写 stderr:与 stdout 分离,便于调用方单独重定向
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 传了 handlers 时 basicConfig 的 format 参数会被忽略,格式由上面的 formatter 决定
    logging.basicConfig(level=level, handlers=[file_handler, console_handler])
    return logging.getLogger(__name__)
