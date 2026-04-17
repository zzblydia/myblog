import logging
from datetime import datetime
from pathlib import Path


def init_logging(level: int = logging.INFO) -> logging.Logger:
    """Initialize file-only logging with a timestamp-based filename.

    Returns the root logger configured to write to
    <script_dir>/<YYYYMMDD_HHMMSS>.log at the given level.
    Console output is intentionally suppressed.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = Path(__file__).parent / f"{timestamp}.log"

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )
    return logging.getLogger(__name__)
