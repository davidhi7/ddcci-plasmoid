from __future__ import annotations

from unittest import mock

import pytest

from ddcci_plasmoid_backend.adapters import adapters
from ddcci_plasmoid_backend.adapters.adapters import (
    _ensure_valid_property_value,
    _get_adapter_type,
    _limit_continuous_property_value,
    _validate_non_continuous_property_value,
)
from ddcci_plasmoid_backend.adapters.monitor_adapter import Monitor, Property
from ddcci_plasmoid_backend.errors import IllegalPropertyValueError, UnsupportedPropertyError

sample_monitor = Monitor.model_validate(
    {
        "name": "test",
        "adapter": "ddcci",
        "id": 1,
        "property_values": {
            Property.BRIGHTNESS: {"value": 50, "min_value": 0, "max_value": 100},
            Property.POWER_MODE: {"value": 1, "choices": [1, 2, 3, 4, 5]},
        },
    }
)


def test_get_adapter_type():
    with mock.patch.object(
        adapters, "monitor_adapter_classes", {"test": "testadapter"}
    ):
        assert _get_adapter_type("test") == "testadapter"


def test_get_adapter_type_invalid_type():
    with pytest.raises(
        ValueError, match="`invalidadapter12345` is not a valid monitor adapter type"
    ):
        _get_adapter_type("invalidadapter12345")


def test_validate_non_continuous_property_value():
    assert _validate_non_continuous_property_value(
        sample_monitor, Property.POWER_MODE, 1
    )
    assert (
        _validate_non_continuous_property_value(sample_monitor, Property.POWER_MODE, 10)
        is False
    )


def test_validate_non_continuous_property_value_invalid_property():
    with pytest.raises(UnsupportedPropertyError):
        _validate_non_continuous_property_value(sample_monitor, Property.CONTRAST, 50)


def test_limit_continuous_property_value():
    assert (
        _limit_continuous_property_value(sample_monitor, Property.BRIGHTNESS, 50) == 50
    )
    assert (
        _limit_continuous_property_value(sample_monitor, Property.BRIGHTNESS, 150)
        == 100
    )
    assert (
        _limit_continuous_property_value(sample_monitor, Property.BRIGHTNESS, -50) == 0
    )


def test_limit_continuous_property_value_invalid_property():
    with pytest.raises(UnsupportedPropertyError):
        _limit_continuous_property_value(sample_monitor, Property.CONTRAST, 50)


def test_ensure_valid_property_value_noncontinuous():
    with mock.patch.object(
        adapters, "_validate_non_continuous_property_value", return_value=False
    ):
        with pytest.raises(IllegalPropertyValueError):
            _ensure_valid_property_value(sample_monitor, Property.POWER_MODE, 1)


def test_ensure_valid_property_value_continuous():
    with mock.patch.object(
        adapters, "_limit_continuous_property_value", return_value=100
    ):
        assert (
            _ensure_valid_property_value(sample_monitor, Property.BRIGHTNESS, 1) == 100
        )


def test_ensure_valid_property_value_invalid_property():
    with pytest.raises(UnsupportedPropertyError):
        _ensure_valid_property_value(sample_monitor, Property.CONTRAST, 50)
