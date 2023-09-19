from enum import Enum
from pathlib import Path


class CacheFiles(Enum):
    DETECT = Path("~/.cache/ddcci_plasmoid/detect.json").expanduser()
