# KDE Plasma Widget for external monitor brightness adjustment

![Screenshot](https://raw.githubusercontent.com/davidhi7/ddcci-plasmoid/main/screenshots/banner.png)

* This widget allows you to adjust the brightness of external monitors. We accomplish that using [DDC/CI](https://en.wikipedia.org/wiki/Display_Data_Channel#DDC/CI), a protocol that allows your computer to control monitors and change options like the brightness or contrast.
* A seamless integration into the Plasma desktop is a major goal of this project. The widget is versatile and can be used as a standalone widget or integrated into the system tray.
* Notebook monitors are currently unsupported because they use different interfaces to communicate with the operating system.

## Requirements

* Python 3.8 or newer
* [fasteners](https://pypi.org/project/fasteners/)
* ddcutil 1.4.1 or newer (older versions may work but caused issues in the past)

## This package acts as the backend for the widget.
For a full installation guide, refer to the [GitHub repository](https://github.com/davidhi7/ddcci-plasmoid).