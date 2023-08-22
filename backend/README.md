# KDE Plasma Widget for external monitor brightness adjustment

![Screenshot](https://raw.githubusercontent.com/davidhi7/ddcci-plasmoid/main/screenshots/banner.png)

* This widget allows you to adjust the brightness of external monitors. We accomplish that
  using [DDC/CI](https://en.wikipedia.org/wiki/Display_Data_Channel#DDC/CI), a protocol that allows your computer to
  control monitors and change options like the brightness or contrast.
* A seamless integration into the Plasma desktop is a major goal of this project. The widget is versatile and can be
  used as a standalone widget or integrated into the system tray.
* Notebook monitors are currently unsupported because they use different interfaces to communicate with the operating
  system.

This package serves as the backend for the widget.
For a full installation guide, refer to the [GitHub repository](https://github.com/davidhi7/ddcci-plasmoid).

## Backend

The backend is a CLI application that is invoked by the widget frontend to query connected monitors and set their
properties, such as the brightness or contrast.

### detect monitors

```bash
$ ddcci_plasmoid_backend detect ddcci
{
  "command": "detect",
  "response": {
    "ddcci": {
      "9": {
        "name": "DELL S2721DGF",
        "property_values": {
          "brightness": {
            "value": 65,
            "min": 0,
            "max": 100
          },
          "contrast": {
            "value": 75,
            "min": 0,
            "max": 100
          },
          "power_mode": {
            "value": 1,
            "accepted": [
              1,
              4,
              5
            ]
          }
        },
        "ddcutil_id": 1,
        "bus_id": 9,
        "vcp_capabilities": {
          "10": null,
          "12": null,
          "D6": [
            1,
            4,
            5
          ]
        }
      }
    }
  }
}
```

Every detected monitor regardless of the adapter features values for the keys `name` and `property_values`. The integer
key of the display is used to identify the monitor when setting its properties.

### set properties

```bash
$ ddcci_plasmoid_backend set ddcci 9 brightness 100
```

### Available adapters

#### ddcci: Communication with DDC/CI compliant monitors using ddcutil

| Option name                    | Description                                                                                                                                                                                                                        | Default value |
|--------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| ddcci_ddcutil_executable       | Command to invoke the ddcutil CLI                                                                                                                                                                                                  | `ddcutil`     |
| ddcci_ddcutil_sleep_multiplier | Floating point number that specifies how long ddcutil waits for responses from monitors. The value is passed to the ddcutil `--sleep-multiplier` option, see https://www.ddcutil.com/performance_options/#option-sleep-multiplier. | `1.0`         |
| ddcci_ddcutil_no_verify        | Boolean value, skip setvcp value verification by ddcutil if set to true. See https://www.ddcutil.com/command_setvcp/#option-noverify.                                                                                              | `false`       |
| ddcci_brute_force_attempts     | If DDC communication failed, try again N times before giving up. Workaround for [#28](https://github.com/davidhi7/ddcci-plasmoid/issues/28).                                                                                       | `0`           |

###     
