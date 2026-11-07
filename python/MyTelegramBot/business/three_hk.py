"""3HK DIY 预付费卡余额与到期时间查询。

只负责"拿到要发送的文本":不 import telegram、不读配置文件、不发送消息。
凭证由调用方从 config/config.json 读取后以参数传入;本模块不接触配置文件,
也不在日志中输出邮箱、密码、cookie 或响应体。

查询链路来自 3HK DIY 前端(v0.68.0):
  POST   /ft-prepaid-pro/user/login/
  GET    /ft-prepaid-pro/user/getProfile
  GET    /ft-prepaid-pro/sim/{subscriptionId}/WalletBalances
  DELETE /ft-prepaid-pro/user/logout          (best-effort)

套餐流量暂未实现:当前账号没有订购套餐。后续可从
subscription.subscriptionOffers[].subscriptionProducts[].matrixxBalanceInfos[]
中解析。
"""

import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

_API_BASE = "https://www.three.com.hk/ft-prepaid-pro"
_LOGIN_URL = f"{_API_BASE}/user/login/"
_PROFILE_URL = f"{_API_BASE}/user/getProfile"
_WALLET_URL = f"{_API_BASE}/sim/{{subscription_id}}/WalletBalances"
_LOGOUT_URL = f"{_API_BASE}/user/logout"

_REQUEST_TIMEOUT = 30
_LOGOUT_TIMEOUT = 10
_HK_TZ = timezone(timedelta(hours=8))

# 前端使用的平台标识;3HK 升级前端后此值可能需要同步更新
_PLATFORM_VERSION = "0.68.0"

_BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
    "Content-Type": "application/json",
    "Origin": "https://www.three.com.hk",
    "Referer": "https://www.three.com.hk/prepaid/DIY/tc/account/login/",
    "platformId": "PREPAID_WEB",
    "platformVersion": _PLATFORM_VERSION,
    "Pragma": "no-cache",
}

# 部分 ISO 时间会带 9 位小数,Python 3.10 的 fromisoformat 只接受最多 6 位
_ISO_FRACTION_RE = re.compile(r"(\.\d{6})\d+")


class _ThreeHkError(Exception):
    """可直接展示给用户的业务错误;不需要打印 traceback。"""


@dataclass(frozen=True)
class ThreeHkAccount:
    """查询结果中的原始字段;文本排版由 format_three_hk_message 负责。"""

    balance_hkd: Decimal | None   # None 表示余额接口失败,不影响到期时间
    expiry: str                   # 已格式化;空串表示 API 未提供


def query_3hk_data(
    email: str,
    password: str,
    subscription_id: str = "",
) -> str:
    """查询并返回待发送文本,永不抛异常。

    凭证由调用方传入,本函数不读取配置文件。失败时返回 "查询失败: <原因>",
    这样发送侧不需要重复写 try/except。
    """
    session = _build_session()
    logged_in = False
    try:
        _login(session, email, password)
        logged_in = True

        subscription = _get_subscription(session, subscription_id)
        account = ThreeHkAccount(
            balance_hkd=_get_wallet_balance(session, subscription),
            expiry=_format_expiry(str(subscription.get("subsEndDate") or "")),
        )
        return format_three_hk_message(account)
    except _ThreeHkError as exc:
        # 业务错误是预期分支(密码错误、限流等),只记 warning,不打印 traceback
        logger.warning("3HK query failed: %s", exc)
        return f"查询失败: {exc}"
    except requests.Timeout:
        # 网络超时很常见,完整堆栈只会污染日志
        logger.warning("3HK query timeout")
        return "查询失败: 请求超时"
    except requests.RequestException as exc:
        # DNS 失败、连接中断等:保留原因,但不打印 urllib3 的完整堆栈
        logger.warning("3HK network error: %s", exc)
        return f"查询失败: 网络错误: {exc}"
    except Exception as exc:  # 解析等未预期异常统一在此收口
        logger.exception("3HK query failed")
        return f"查询失败: {exc}"
    finally:
        if logged_in:
            _safe_logout(session)
        session.close()


def format_three_hk_message(account: ThreeHkAccount) -> str:
    """拼装待发送文本;余额查询失败时仍展示到期时间。"""
    lines = ["3HK DIY"]
    if account.balance_hkd is None:
        lines.append("余额: 查询失败")
    else:
        lines.append(f"余额: HK$ {account.balance_hkd:.2f}")
    lines.append(f"到期时间: {account.expiry or '未提供'}")
    return "\n".join(lines)


def _build_session() -> requests.Session:
    """创建带公共请求头的会话;cookie 由 requests 自动维护。"""
    session = requests.Session()
    session.headers.update(_BASE_HEADERS)
    return session


def _login(session: requests.Session, email: str, password: str) -> None:
    """登录 3HK;任何失败都转成带用户可读原因的 _ThreeHkError。

    allow_redirects=False 是刻意的:避免 POST 凭证被 307/308 重定向到其他域名。
    """
    payload = {
        "id": email,
        "password": password,
        "showProf": True,
        "rememberMe": False,
        "forceLogin": False,
    }

    response = session.post(
        _LOGIN_URL,
        json=payload,
        timeout=_REQUEST_TIMEOUT,
        allow_redirects=False,
    )
    logger.debug("3HK login status: %s", response.status_code)

    # 400 的响应体为空,不能依赖 JSON 解析来判断失败原因
    if response.status_code == 200:
        _ensure_not_html(response, "登录")
        # 后续请求模拟从登录页进入 dashboard,与浏览器行为一致
        session.headers["Referer"] = (
            "https://www.three.com.hk/prepaid/DIY/tc/account/dashboard/"
        )
        return
    if response.status_code == 400:
        raise _ThreeHkError("账号或密码错误")
    if response.status_code == 406:
        raise _ThreeHkError("账号已在其他设备登录")
    if response.status_code == 429:
        raise _ThreeHkError("登录过于频繁，请稍后再试")
    if response.status_code == 503:
        raise _ThreeHkError("3HK 服务维护中")
    if 300 <= response.status_code < 400:
        raise _ThreeHkError(f"登录返回重定向 HTTP {response.status_code}，已中止")
    raise _ThreeHkError(f"登录失败 HTTP {response.status_code}")


def _get_subscription(
    session: requests.Session,
    subscription_id: str,
) -> dict:
    """读取用户资料并返回选定的 PREPAID 订阅。"""
    response = session.get(
        _PROFILE_URL,
        timeout=_REQUEST_TIMEOUT,
        allow_redirects=False,
    )
    logger.debug("3HK profile status: %s", response.status_code)
    _raise_for_api_status(response, "获取用户资料")

    data = _response_json(response, "获取用户资料")
    subscriptions = _extract_subscriptions(data)
    prepaid = [
        item
        for item in subscriptions
        if str(item.get("serviceType") or "").upper() == "PREPAID"
    ]
    if not prepaid:
        raise _ThreeHkError("未找到 PREPAID 订阅")

    # 多卡场景优先使用调用方指定的订阅
    if subscription_id:
        for item in prepaid:
            if str(item.get("subscriptionId") or "") == subscription_id:
                return item
        raise _ThreeHkError("未找到指定的订阅")

    # 与网页一致:优先主卡,其次第一条
    for item in prepaid:
        if item.get("primarySubsInd"):
            return item
    return prepaid[0]


def _extract_subscriptions(data: object) -> list[dict]:
    """兼容直接返回 subscriptions 或包一层 data/user 的响应。"""
    if isinstance(data, dict):
        for key in ("data", "user"):
            nested = data.get(key)
            if isinstance(nested, dict) and isinstance(nested.get("subscriptions"), list):
                data = nested
                break

        subscriptions = data.get("subscriptions")
        if isinstance(subscriptions, list):
            return [item for item in subscriptions if isinstance(item, dict)]

    raise _ThreeHkError("用户资料中没有 subscriptions")


def _get_wallet_balance(
    session: requests.Session,
    subscription: dict,
) -> Decimal | None:
    """查询钱包余额;失败时返回 None,由调用方降级展示到期时间。"""
    subscription_id = str(subscription.get("subscriptionId") or "")
    if not subscription_id:
        logger.warning("3HK subscription has no subscriptionId, skip wallet query")
        return None

    url = _WALLET_URL.format(subscription_id=quote(subscription_id, safe=""))
    try:
        response = session.get(
            url,
            timeout=_REQUEST_TIMEOUT,
            allow_redirects=False,
        )
        logger.debug("3HK wallet status: %s", response.status_code)
        _raise_for_api_status(response, "查询余额")

        data = _response_json(response, "查询余额")
        total = Decimal("0")
        for item in _extract_wallet_items(data):
            # 与网页钱包一致:账单余额不计入可用余额
            if _is_true(item.get("carrierBillBalance")):
                continue
            amount = _to_decimal(item.get("amount"))
            if amount is not None:
                total += amount
        return total
    except Exception as exc:
        # 余额是附加信息,失败不应阻断到期时间
        logger.warning("3HK wallet query failed: %s", exc)
        return None


def _extract_wallet_items(data: object) -> list[dict]:
    """兼容数组或包一层 data/walletBalances/balances 的响应。"""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    if isinstance(data, dict):
        for key in ("data", "walletBalances", "balances"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    raise _ThreeHkError("余额响应格式不正确")


def _format_expiry(raw: str) -> str:
    """把 ISO 时间格式化为 YYYY-MM-DD HH:MM;解析失败时原样返回。"""
    value = raw.strip()
    if not value:
        return ""

    normalized = _ISO_FRACTION_RE.sub(r"\1", value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return value

    # 带时区的时间统一转成香港时间;naive 时间按香港本地时间处理
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(_HK_TZ)
    return parsed.strftime("%Y-%m-%d %H:%M")


def _raise_for_api_status(response: requests.Response, action: str) -> None:
    """把常见的 HTTP 状态翻译成用户可读错误;不读取响应体。"""
    status = response.status_code
    if status == 200:
        return
    if status == 401:
        raise _ThreeHkError(f"{action}: 登录状态失效")
    if status == 403:
        raise _ThreeHkError(f"{action}: 无权限")
    if status == 429:
        raise _ThreeHkError(f"{action}: 请求过于频繁")
    if status == 503:
        raise _ThreeHkError(f"{action}: 3HK 服务维护中")
    if 300 <= status < 400:
        raise _ThreeHkError(f"{action}: 返回重定向 HTTP {status}")
    raise _ThreeHkError(f"{action}: HTTP {status}")


def _response_json(response: requests.Response, action: str) -> object:
    """解析 JSON;HTML 通常意味着被 Cloudflare 拦截或会话失效。"""
    _ensure_not_html(response, action)
    try:
        return response.json()
    except ValueError as exc:
        raise _ThreeHkError(f"{action}: 响应不是合法 JSON") from exc


def _ensure_not_html(response: requests.Response, action: str) -> None:
    content_type = (response.headers.get("content-type") or "").lower()
    if "text/html" in content_type:
        raise _ThreeHkError(f"{action}: 3HK 返回 HTML 页面，可能被拦截")


def _to_decimal(value: object) -> Decimal | None:
    """把金额转成 Decimal;支持带千分位的字符串,非法值返回 None。"""
    if value is None or value == "":
        return None
    try:
        result = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def _is_true(value: object) -> bool:
    """兼容 bool 与字符串形式的布尔值。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "y")
    return bool(value)


def _safe_logout(session: requests.Session) -> None:
    """登出当前会话;失败只记 debug,不影响查询结果。"""
    try:
        session.delete(
            _LOGOUT_URL,
            timeout=_LOGOUT_TIMEOUT,
            allow_redirects=False,
        )
    except Exception as exc:
        logger.debug("3HK logout failed: %s", exc)


if __name__ == "__main__":
    # 单文件调试入口:凭证只从环境变量读取,不写入代码或日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    debug_email = os.environ.get("THREE_HK_EMAIL", "")
    debug_password = os.environ.get("THREE_HK_PASSWORD", "")
    if not debug_email or not debug_password:
        print("请设置环境变量 THREE_HK_EMAIL / THREE_HK_PASSWORD")
        sys.exit(1)

    print(query_3hk_data(debug_email, debug_password))
