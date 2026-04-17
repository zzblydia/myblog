import json
from pathlib import Path


def load_config(config_path: Path | None = None) -> dict:
    """Load configuration from config.json in the script directory.

    Args:
        config_path: Optional explicit path. Defaults to config.json
                     next to this file.

    Returns:
        Parsed config dict with at least the keys:
        bot_token, admin_user_id, order_id, run_mode.
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
