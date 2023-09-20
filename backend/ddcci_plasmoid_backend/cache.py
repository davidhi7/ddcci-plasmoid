import os.path
from enum import Enum
from pathlib import Path

CACHE_DIR = (
    Path(os.path.expandvars("$XDG_CACHE_HOME"))
    if "XDG_CACHE_HOME" in os.environ
    else Path("~/.cache").expanduser()
)


class CacheFiles(Enum):
    DETECT = CACHE_DIR / "ddcci_plasmoid/detect.json"
