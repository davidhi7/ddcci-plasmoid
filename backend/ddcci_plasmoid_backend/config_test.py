from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ddcci_plasmoid_backend import config
from ddcci_plasmoid_backend.errors import ConfigurationError


@pytest.fixture
def _mock_config_scheme():
    old_value = config.CONFIG_SCHEME
    config.CONFIG_SCHEME = {
        "section1": {
            "key1": {"type": str, "default": "value1"},
            "key2": {"type": int, "default": 2},
        },
        "section2": {"key1": {"type": str, "default": "value1"}},
    }
    yield
    config.CONFIG_SCHEME = old_value


@pytest.mark.usefixtures("_mock_config_scheme")
def test_create_config():
    config_object = config.init(None)
    assert config_object.sections() == ["section1", "section2"]
    assert config_object["section1"]["key1"] == "value1"
    assert config_object["section1"]["key2"] == "2"
    assert config_object["section2"]["key1"] == "value1"


@pytest.mark.usefixtures("_mock_config_scheme")
def test_read_file():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as file:
        config_object = config.init(None)
        config_object["section2"]["key2"] = "value2"
        config_object.write(file)

    config_from_file = config.init(Path(file.name))
    assert config_object._sections == config_from_file._sections

    Path(file.name).unlink()


@pytest.mark.usefixtures("_mock_config_scheme")
def test_set_config_value():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as file:
        config_object = config.init(None)
        config.set_config_value(
            config_object, "section1", "key2", "3", save_file_path=Path(file.name)
        )

    assert config_object["section1"]["key2"] == "3"
    assert config_object._sections == config.init(Path(file.name))._sections

    Path(file.name).unlink()


@pytest.mark.usefixtures("_mock_config_scheme")
def test_set_config_value_errors():
    config_object = config.init(None)
    with pytest.raises(ConfigurationError, match="Section"):
        config.set_config_value(config_object, "wrong-section", "key1", "value")
    with pytest.raises(ConfigurationError, match="Key"):
        config.set_config_value(config_object, "section1", "wrong-key", "value")
    with pytest.raises(ConfigurationError, match="Value"):
        config.set_config_value(config_object, "section1", "key2", "not-an-int")
