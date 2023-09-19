import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SerialNumbers:
    """
    Dataclass for identifying a monitor by its `Serial number` as well as `Binary serial number`
    EDID value reported by ddcutil to look for duplicate monitors. Issue #1 shows that comparing by
    Serial number only is not sufficient, as the monitors of the reporter only reported a binary
     serial number.
    """

    serial_number: Optional[str]
    binary_serial_number: Optional[str]

    def __post_init__(self) -> None:
        # From a string like '123456 (0x234567)' extract the '123456' part
        if not self.binary_serial_number:
            return
        pattern = re.compile(r"^([\dA-Za-z]+) \(0x[\dA-Za-z]+\)\s*$")
        if (value := pattern.findall(self.binary_serial_number)) and len(value) == 1:
            # Remove stuff like leading zeros so that binary serial number strings with identical
            # numbers are always equal
            try:
                self.binary_serial_number = str(int(value[0]))
            except ValueError:
                logger.warning(
                    f"Failed to parse binary serial number `{self.binary_serial_number}`"
                )

    def __eq__(self, other: "SerialNumbers") -> bool:
        """
        Compare two instances. Two instances are equal, if both the serial number and the binary
        serial number is equal and at least one of them is not `None` or empty.

        Args:
            other: Instance to compare to

        Returns:
            `True` if both instances are equal, otherwise `False`
        """
        if self is other:
            return True
        if not self.serial_number and not self.binary_serial_number:
            return False
        return (
            self.serial_number == other.serial_number
            and self.binary_serial_number == other.binary_serial_number
        )
