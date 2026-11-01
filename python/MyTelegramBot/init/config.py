"""配置读取。

配置文件固定位于 <项目根>/config/config.json,只读真实配置,
不回退到 config.example.json —— 避免占位值被误当成有效配置使用。
"""

import json
import logging
from pathlib import Path

# init/ 的上两级即项目根;若将来把 init/ 再嵌一层,此处必须同步修改
_PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "config.json"

log = logging.getLogger(__name__)


def load_config(config_path: Path | None = None) -> dict:
    """读取配置;文件缺失时抛出带修复提示的 FileNotFoundError。"""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH

    if not path.is_file():
        raise FileNotFoundError(
            f"配置文件不存在: {path};"
            "请执行 cp config/config.example.json config/config.json 后填入真实值"
        )

    log.info("Loading config from %s", path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
