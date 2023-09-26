from __future__ import annotations

import json
import logging
import os.path
from enum import Enum
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

CACHE_DIR: Final[Path] = (
    Path(os.path.expandvars("$XDG_CACHE_HOME"))
    if "XDG_CACHE_HOME" in os.environ
    else Path("~/.cache").expanduser()
)


class CacheFiles(Enum):
    DETECT = CACHE_DIR / "ddcci_plasmoid/detect.json"


cached_data: dict[CacheFiles, dict] = {}

for cache_file in CacheFiles:
    if not cache_file.value.is_file():
        logger.warning("Cache file `%s` does not exist", cache_file.value)
        continue
    with cache_file.value.open() as file:
        cached_data[cache_file] = json.load(file)
