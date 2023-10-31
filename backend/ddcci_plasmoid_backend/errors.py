from __future__ import annotations

from ddcci_plasmoid_backend.adapters.monitor_adapter import (
    CONTINUOUS_PROPERTIES,
    AdapterIdentifier,
    MonitorIdentifier,
    Property,
)
from ddcci_plasmoid_backend.cache import CacheFile


class ConfigurationError(Exception):
    """Error related to configuration sections, keys and values"""


class MissingCacheError(Exception):
    """Errors related to missing cache data"""

    def __init__(self, description: CacheFile | str) -> None:
        if isinstance(description, CacheFile):
            cache_file: CacheFile = description
            msg = f"Cache `{cache_file}` unavailable (path: {cache_file.value.path})"
        else:
            msg = description
        super().__init__(msg)


class UnsupportedPropertyError(Exception):
    """Monitor does not support a property"""

    def __init__(
        self, adapter: AdapterIdentifier, id: MonitorIdentifier, property: Property
    ) -> None:
        super().__init__(
            f"Monitor `{adapter}.{id}` does not support property `{property}`"
        )


class IllegalPropertyValueError(Exception):
    """Monitor does not support a value as a property value"""

    def __init__(
        self,
        adapter: AdapterIdentifier,
        id: MonitorIdentifier,
        property: Property,
        value: int,
    ) -> None:
        is_continuous = property in CONTINUOUS_PROPERTIES
        msg = (
            f"Monitor `{adapter}.{id}` does not support the value `{value}` for "
            f" {'continuous' if is_continuous else 'non-continuous'} property `{property}`"
        )
        super().__init__(msg)


class IllegalArgumentError(ValueError):
    """An illegal value for an argument was provided"""


class DdcutilError(OSError):
    """A ddcutil command failed"""
