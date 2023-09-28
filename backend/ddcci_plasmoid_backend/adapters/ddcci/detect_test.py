from __future__ import annotations

import pytest

from ddcci_plasmoid_backend import subprocess_wrappers
from ddcci_plasmoid_backend.adapters.ddcci.detect import (
    _get_ddcutil_monitor_id,
    _get_monitor_identification,
    _get_vcp_value,
    _parse_capabilities,
)
from ddcci_plasmoid_backend.adapters.ddcci.serial_numbers import SerialNumbers
from ddcci_plasmoid_backend.tree import Node


def test_get_monitor_identification():
    parent = Node(None, 0, key="Display 1")
    edid_child = Node(parent, 1, key="EDID synopsis")
    Node(edid_child, 2, key="Serial number", value="ser_num")
    Node(edid_child, 2, key="Binary serial number", value="bin_ser_num")
    assert _get_monitor_identification(parent) == SerialNumbers(
        serial_number="ser_num", binary_serial_number="bin_ser_num"
    )


def test_get_ddcutil_monitor_id():
    assert _get_ddcutil_monitor_id(Node(None, 0, key="Display 1", value="")) == 1
    assert _get_ddcutil_monitor_id(Node(None, 0, key="Display 1234", value="")) == 1234


def test_get_ddcutil_monitor_id_exception():
    with pytest.raises(ValueError):
        _get_ddcutil_monitor_id(Node(None, 0, key="Invalid display", value=""))
    with pytest.raises(ValueError):
        _get_ddcutil_monitor_id(
            Node(
                None,
                0,
                key="This is some sample text unrelated to ddcutil",
                value="random value",
            )
        )


async def test_get_vcp_value_continuous(
    monkeypatch, return_coroutine, return_command_output, default_ddcutil_wrapper
):
    monkeypatch.setattr(
        subprocess_wrappers,
        "async_subprocess_wrapper",
        lambda cmd, logger: return_coroutine(
            return_command_output(stdout="VCP 10 C 45 100")
        ),
    )
    assert await _get_vcp_value(default_ddcutil_wrapper, 0, 0x10) == 45


async def test_get_vcp_value_noncontinuous(
    monkeypatch, return_coroutine, return_command_output, default_ddcutil_wrapper
):
    monkeypatch.setattr(
        subprocess_wrappers,
        "async_subprocess_wrapper",
        lambda cmd, logger: return_coroutine(
            return_command_output(stdout="VCP D6 SNC x01")
        ),
    )
    assert await _get_vcp_value(default_ddcutil_wrapper, 0, 0xD6) == 1


async def test_parse_capabilities(
    monkeypatch, return_coroutine, return_command_output, default_ddcutil_wrapper
):
    vcp_feature_string = (
        "Unparsed capabilities string: (prot(monitor)type(LCD)model(S2721DGFA)cmds(01"
        " 02 03 07 0C E3 F3)vcp(02 04 05 08 10 12 14(05 08 0B 0C) 16 18 1A 52 60(0F 11"
        " 12 ))mswhql(1)asset_eep(40)mccs_ver(2.1))"
    )
    monkeypatch.setattr(
        subprocess_wrappers,
        "async_subprocess_wrapper",
        lambda cmd, logger: return_coroutine(
            return_command_output(stdout=vcp_feature_string)
        ),
    )
    assert await _parse_capabilities(default_ddcutil_wrapper, 0) == {
        0x02: None,
        0x04: None,
        0x05: None,
        0x08: None,
        0x10: None,
        0x12: None,
        0x14: [0x05, 0x08, 0x0B, 0x0C],
        0x16: None,
        0x18: None,
        0x1A: None,
        0x52: None,
        0x60: [0x0F, 0x11, 0x12],
    }
