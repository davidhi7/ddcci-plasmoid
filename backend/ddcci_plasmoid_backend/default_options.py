from typing import Final

from ddcci_plasmoid_backend.adapters.monitor_adapter import Options

"""
Default values for all options used by monitor adapters.
"""
DEFAULT_OPTIONS: Final[Options] = {
    'ddcutil_executable': 'ddcutil',
    'ddcutil_sleep_multiplier': 1,
    'ddcutil_no_verify': False,
    'brute_force_attempts': 0
}
