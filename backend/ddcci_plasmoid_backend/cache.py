from __future__ import annotations

import json
import logging
import os.path
from dataclasses import dataclass
from enum import Enum
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, Final

from pydantic import BaseModel, ValidationError

from ddcci_plasmoid_backend.adapters.monitor_adapter import (
    AdapterIdentifier,
    Monitor,
    MonitorIdentifier,
)

logger = logging.getLogger(__name__)

CACHE_DIR: Final[Path] = (
    Path(os.path.expandvars("$XDG_CACHE_HOME"))
    if "XDG_CACHE_HOME" in os.environ
    else Path("~/.cache").expanduser()
)


@dataclass
class CacheFileClass:
    path: Path
    model: type[BaseModel]


@dataclass
class DetectOutput(BaseModel):
    data: Dict[AdapterIdentifier, Dict[MonitorIdentifier, Monitor]]


class CacheFile(Enum):
    DETECT_OUTPUT = CacheFileClass(
        path=CACHE_DIR / "ddcci_plasmoid/detect.json", model=DetectOutput
    )


cached_data: dict[CacheFile, BaseModel] = {}


for cache_file in CacheFile:
    if not cache_file.value.path.is_file():
        logger.warning("Cache file `%s` does not exist", cache_file.value)
        continue
    with cache_file.value.path.open() as file:
        try:
            cached_data[cache_file] = cache_file.value.model.model_validate(
                json.load(file)
            )
        except JSONDecodeError:
            logger.exception(f"Failed to parse JSON cache file `{cache_file.value}`")
        except ValidationError:
            logger.exception(
                f"Failed to validate cache file contents `{cache_file.value}` using model "
                f"`{cache_file.value.model.__name__}`"
            )


def write_cache_file(cache_file: CacheFile) -> None:
    cache_file.value.path.parent.mkdir(exist_ok=True)
    with cache_file.value.path.open("w") as file:
        file.write(cache_file.value.model.model_dump_json(cached_data[cache_file]))
