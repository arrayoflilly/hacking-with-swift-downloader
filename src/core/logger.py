from pathlib import Path
from datetime import datetime

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "debug.log"


def _ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def log(msg: str):
    _ensure_log_dir()
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} {msg}\n")
        
def log_reset():
    _ensure_log_dir()
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        pass
