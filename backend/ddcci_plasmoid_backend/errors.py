from __future__ import annotations

from typing import TYPE_CHECKING

from ddcci_plasmoid_backend.adapters.monitor_adapter import (
    AdapterIdentifier,
    MonitorIdentifier,
    Property,
)

if TYPE_CHECKING:
    pass


class ConfigurationError(Exception):
    """Error related to configuration sections, keys and values"""


class MissingCacheError(Exception):
    """Errors related to missing cache data"""


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
        *,
        is_continuous: bool,
    ):
        msg = (
            f"Monitor `{adapter}.{id}` does not support the value `{value}` for "
            f" {'continuous' if is_continuous else 'non-continuous'} property `{property}`"
        )
        super().__init__(msg)
