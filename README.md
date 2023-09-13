# KDE Plasma Widget for external monitor brightness adjustment

![Screenshot](./screenshots/banner.png)

* This widget allows you to adjust the brightness of external monitors. We accomplish that using [DDC/CI](https://en.wikipedia.org/wiki/Display_Data_Channel#DDC/CI), a protocol that allows your computer to control monitors and change options like the brightness or contrast.
* A seamless integration into the Plasma desktop is a major goal of this project. The widget is versatile and can be used as a standalone widget or integrated into the system tray.
* Notebook monitors are currently unsupported because they use different interfaces to communicate with the operating system.

## Requirements

* Python 3.8 or newer
* python library [fasteners](https://pypi.org/project/fasteners/)
* ddcutil 1.4.1 or newer (older versions may work but caused issues in the past)

## Setup

### 1. Load the `i2c-dev` kernel module

DDC/CI communication relies on i²C busses. The i2c-dev kernel module exposes this functionality to the userspace. Most kernel builds should include this module already, so it only needs to be loaded.

Check if it is already loaded:

`$ lsmod | grep i2c_dev`

If it isn't, load it automatically on every boot:

`$ echo i2c-dev | sudo tee /etc/modules-load.d/i2c-dev.conf`

or load it once:

`$ sudo modprobe i2c-dev`

### 2. Install and configure **ddcutil**

ddcutil is a command line utility to control external monitors.
We use ddcutil to detect supported monitors and adjust their brightness.
For additional details, refer to the great [ddcutil documentation](http://www.ddcutil.com/).
Note that additional steps may be required if you are using a NVIDIA GPU, see [Special Nvidia Driver Settings](https://www.ddcutil.com/nvidia/) in the ddcutil documentation.

Install the `ddcutil` from your distribution's repositories. ([Arch Linux](https://archlinux.org/packages/extra/x86_64/ddcutil/))

By default, ddcutil can only be used the the root user.
Little configuration is required to allow non-root users to use it:

`$ sudo usermod -aG i2c <username>`

If the group `i2c` doesn't exit, create it first:

`$ sudo groupadd --system i2c`

Finally, you need to install a udev rule to allow members of the group `i2c` to access to i²c devices: 

`$ sudo cp /usr/share/ddcutil/data/45-ddcutil-i2c.rules /etc/udev/rules.d`

Now, you can verify that ddcutil is working correctly:

`$ ddcutil detect`

The output should look something like that:

```
Display 1
   I2C bus:  /dev/i2c-9
   DRM connector:           card0-DP-1
   EDID synopsis:
      Mfg id:               DEL - Dell Inc.
      Model:                DELL S2721DGF
      Product code:         16857  (0x41d9)
      Serial number:        XXXXXXXX
      Binary serial number: XXXXXXXX (0xXXXXXXXX)
      Manufacture year:     2022,  Week: 35
   VCP version:         2.1

Display 2
   I2C bus:  /dev/i2c-10
   DRM connector:           card0-DP-2
   EDID synopsis:
      Mfg id:               DEL - Dell Inc.
      Model:                DELL U2417H
      Product code:         16615  (0x40e7)
      Serial number:        XXXXXXXX
      Binary serial number: XXXXXXXX (0xXXXXXXXX)
      Manufacture year:     2018,  Week: 22
   VCP version:         2.1
```

### 3. Install the backend ###

Install the backend from PyPI using the following command:

`$ pip install --user ddcci-plasmoid-backend`

You can also use [`pipx`](https://pypa.github.io/pipx/) to install the backend.
This is the recommended option if your distribution doesn't allow `pip` for global packages, see [PEP-668](https://peps.python.org/pep-0668/).

`$ pipx install ddcci-plasmoid-backend`

About [pipx](https://pypa.github.io/pipx/):

> #### Overview: What is pipx?
> pipx is a tool to help you install and run end-user applications written in Python. It's roughly similar to macOS's brew, JavaScript's npx, and Linux's apt.
>
>It's closely related to pip. In fact, it uses pip, but is focused on installing and managing Python packages that can be run from the command line directly as applications.
> #### How is it Different from pip?
>
>pip is a general-purpose package installer for both libraries and apps with no environment isolation. pipx is made specifically for application installation, as it adds isolation yet still makes the apps available in your shell: pipx creates an isolated environment for each application and its associated packages.

### 4. Install the widget itself ###

Install the [official package](https://store.kde.org/p/2015475) from the KDE store or install it directly from the repository:

````bash
$ git clone https://github.com/davidhi7/ddcci-plasmoid.git
$ cd ddcci-plasmoid
$ kpackagetool5 --install plasmoid
# or upgrade the plasmoid:
$ kpackagetool5 --upgrade plasmoid
````

**Note**: If you used `pipx` to install the backend in the previous step, the widget setting `Backend executable command` should be `~/.local/bin/ddcci_plasmoid_backend` (which is the default installation path of pipx).

### 5. Display the widget

This widget can be displayed within the system tray or as a standalone widget.

##### Integrate into systemtray:

Right-click the arrow of the system tray > open settings > go to *Entries* > scroll down to the entry *Display Brightness* and set the visibility according to your preference.

##### standalone widget

Right-click your desktop > click *Add widgets* > search for *Display Brightness* and add the widget to your desktop or panels.

## Common issues

#### Installing the backend with `pip` fails, printing `This environment is externally managed`

Some distributions, most notably Arch Linux, disable the installation of PyPI packages globally using `pip`. In [Step 3](#3-install-the-backend), use the `pipx` alternative instead. 

#### The output of `ddcutil detect` starts with `Unable to open directory /sys/bus/i2c/devices/i2c--1: No such file or directory`

This is a bug in older ddcutil versions which it is fixed in ddcutil v1.4.1. In some cases, it may cause the backend to
fail.

## History

#### v0.1.8 2023-08-26

* Ignore monitors if `VCP version` detection failed by ddcutil (#39)

#### v0.1.7 2023-08-22

* Fix backend command not updating after changing it in the configuration field (#17, thanks CatEricka)

#### v0.1.6 2023-07-09

* Fix backend errors with certain NVIDIA GPUs
* Fix compatibility with Python 3.9 and 3.8

#### v0.1.5 2023-04-16

* Allow integration into the system tray (#2)
* Scrolling while hovering sliders now works (#15, thanks CatEricka)
* Add translations for Simplified Chinese (thanks CatEricka) and German (by myself)
* Lower minimum Python version to 3.8
* Add option to specify the backend executable command manually (thanks CatEricka)

#### v0.1.4 2023-04-12

* Fix error if serial number is missing (#6)

#### v0.1.3 2023-04-11

* Add padding to widget title
* Fix duplicate monitor detection (#1)
* Expand debug output

#### v0.1.2 2023-04-09

* Fix KDE widget configuration not loading

#### v0.1.1 2023-04-09

First public release

