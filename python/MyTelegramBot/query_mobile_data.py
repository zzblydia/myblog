import hmac
import hashlib
import json
import logging
import random
import time

import requests

logger = logging.getLogger(__name__)

QUERY_URL = "https://api.tsimtech.com/tsim/shopify/getGygPlanInfo"

# Per-endpoint credentials extracted from the website frontend JS.
# These are fixed values baked into the public website code.
_TSIM_ACCOUNT = "f8c063b8a1d4478994d7d3cf3073688e"
_TSIM_SECRET  = "d7572b8710eaafcda08696e15d844b78"

_NONCE_CHARS = "ABCDEFGHJKMNOPQRSTUVWXYZabcdefhijkmnopqrstuvwxyz0123456789"

_BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,zh;q=0.6",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "DNT": "1",
    "Priority": "u=1, i",
    "Origin": "https://search.t-sim.hk",
    "Referer": "https://search.t-sim.hk/",
    "Sec-Ch-Ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
}


def _generate_nonce() -> str:
    """Generate a random nonce string (6-30 chars), matching the website JS logic."""
    length = random.randint(6, 30)
    return "".join(random.choice(_NONCE_CHARS) for _ in range(length))


def _build_auth_headers() -> dict:
    """Compute fresh TSIM authentication headers for each request."""
    nonce     = _generate_nonce()
    timestamp = str(int(time.time()))
    message   = (_TSIM_ACCOUNT + nonce + timestamp).encode()
    signature = hmac.new(_TSIM_SECRET.encode(), message, hashlib.sha256).hexdigest()
    return {
        "TSIM-ACCOUNT"  : _TSIM_ACCOUNT,
        "TSIM-NONCE"    : nonce,
        "TSIM-TIMESTAMP": timestamp,
        "TSIM-SIGN"     : signature,
    }


def query_singtel_data(order_id: str) -> str:
    """Query mobile data plan info and return a formatted message.

    The API returns result as a list; we use the first element.
    Only fields that are present and parseable are included in the output.
    """
    headers = {**_BASE_HEADERS, **_build_auth_headers()}
    params  = {"reference": order_id}

    logger.debug("Request URL: %s", QUERY_URL)
    logger.debug("Request params: %s", params)
    logger.debug("Request headers: %s", json.dumps(headers, ensure_ascii=False))

    response = requests.get(QUERY_URL, params=params, headers=headers, timeout=30)

    logger.debug("Response status: %s", response.status_code)
    logger.debug("Response body: %s", response.text)

    response.raise_for_status()
    data = response.json()

    if data.get("code") != 1:
        raise ValueError(f"API error {data.get('code')}: {data.get('msg', 'unknown error')}")

    result_list = data.get("result", [])
    if not result_list:
        raise ValueError("API returned empty result list")

    result = result_list[0]
    lines  = []

    # 套餐名称
    plan_name = result.get("channel_dataplan_name")
    if plan_name is not None:
        lines.append(f"套餐名称: {plan_name}")

    # 失效时间 — already a formatted string, e.g. "2027-03-06 22:32:08"
    expire_time = result.get("expire_time")
    if expire_time:
        lines.append(f"失效时间: {expire_time}")

    # 用量 (MB)
    data_usage = result.get("data_usage")
    if data_usage is not None:
        try:
            lines.append(f"用量: {float(data_usage):.2f} M")
        except ValueError as e:
            logger.warning("Failed to parse data_usage %s: %s", data_usage, e)

    if not lines:
        raise ValueError("No usable fields found in API response")

    return "\n".join(lines)
