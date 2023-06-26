# KDE Plasma Widget for external monitor brightness adjustment

![Screenshot](https://raw.githubusercontent.com/davidhi7/ddcci-plasmoid/main/screenshots/banner.png)

* This widget allows you to adjust the brightness of external monitors. We accomplish that using [DDC/CI](https://en.wikipedia.org/wiki/Display_Data_Channel#DDC/CI), a protocol that allows your computer to control monitors and change options like the brightness or contrast.
* A seamless integration into the Plasma desktop is a major goal of this project. The widget is versatile and can be used as a standalone widget or integrated into the system tray.
* Notebook monitors are currently unsupported because they use different interfaces to communicate with the operating system.

This package serves as the backend for the widget.
For a full installation guide, refer to the [GitHub repository](https://github.com/davidhi7/ddcci-plasmoid).

## Backend

The backend is a CLI application that is executed by the widget frontend to query connected monitors and set their properties, such as the brightness or contrast.

### detect monitors

```
$ python -m ddcci_plasmoid_backend detect ddcci
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
# the "vcp_capabilities" list was shortened for readability
```

### set properties
