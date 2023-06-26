import pytest

from ddcci_plasmoid_backend.adapters.ddcci.SerialNumbers import SerialNumbers as SN


def test_equal():
    sn_1 = SN('123', 'abc')
    sn_2 = SN('123', 'abc')

    assert sn_1 == sn_2
    assert sn_1 == sn_1


def test_not_equal():
    sn = SN('1', '2')
    assert sn != SN('1', None)
    assert sn != SN(None, '2')
    assert sn != SN('3', '4')

    assert SN('', '') != SN('', '')

    assert SN(None, None) != SN(None, None)
    assert SN('1', None) != SN(None, None)
    assert SN(None, '1') != SN(None, None)


def test_parse_binary_serial_number():
    id = SN('12345', '12345 (0x67890Abc)')
    assert id.binary_serial_number == '12345'


def test_parse_binary_serial_number_fail():
    assert SN('12345', '12345 (67890)').binary_serial_number == '12345 (67890)'
