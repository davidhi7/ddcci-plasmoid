from ddcci_plasmoid_backend.adapters.ddcci.serial_numbers import SerialNumbers


def test_equal():
    sn_1 = SerialNumbers('123', 'abc')
    sn_2 = SerialNumbers('123', 'abc')

    assert sn_1 == sn_2
    assert sn_1 == sn_1  # noqa: PLR0124 => We test the custom __eq__ function


def test_not_equal():
    sn = SerialNumbers('1', '2')
    assert sn != SerialNumbers('1', None)
    assert sn != SerialNumbers(None, '2')
    assert sn != SerialNumbers('3', '4')

    assert SerialNumbers('', '') != SerialNumbers('', '')

    assert SerialNumbers(None, None) != SerialNumbers(None, None)
    assert SerialNumbers('1', None) != SerialNumbers(None, None)
    assert SerialNumbers(None, '1') != SerialNumbers(None, None)


def test_parse_binary_serial_number():
    id = SerialNumbers('12345', '12345 (0x67890Abc)')
    assert id.binary_serial_number == '12345'


def test_parse_binary_serial_number_fail():
    assert SerialNumbers('12345', '12345 (67890)').binary_serial_number == '12345 (67890)'
