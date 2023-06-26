from enum import Enum

from ddcci_plasmoid_backend import Property


class FeatureCode(Enum):
    BRIGHTNESS = 0x10
    CONTRAST = 0x12
    POWER_MODE = 0xD6


property_feature_codes = {
    Property.BRIGHTNESS: FeatureCode.BRIGHTNESS,
    Property.CONTRAST: FeatureCode.CONTRAST,
    Property.POWER_MODE: FeatureCode.POWER_MODE
}


class PowerModeValues(Enum):
    POWER_ON = 0x01
    DPMS_STANDBY = 0x02
    DPMS_SUSPEND = 0x03
    POWER_OFF = 0x04
    WRITE_ONLY_POWER_OFF = 0x05
