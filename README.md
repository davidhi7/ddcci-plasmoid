# KDE Plasma Widget for external monitor brightness adjustment

![Screenshot](./screenshots/banner.png)

## Setup

### 1. Load the `i2c-dev` kernel module

Note: Most kernel builds should include this module by default.

Check if it is already loaded:

`$ lsmod | grep i2c_dev`

If it isn't, load it automatically on every boot:

`$ echo i2c-dev | sudo tee /etc/modules-load.d/i2c-dev.conf`

or load it once:

`$ sudo modprobe i2c-dev`

### 2. Install and configure **ddcutil**

ddcutil is a commandline utility to control external monitors.
This widget uses ddcutil to detect supported monitors and adjust their brightness.
For additional details, refer to the great [ddcutil documentation](http://www.ddcutil.com/).

Install the `ddcutil` from your distribution's repositories. ([Arch Linux](https://archlinux.org/packages/extra/x86_64/ddcutil/))

By default, ddcutil can only be used the the root user.
Little configuration is required to allow non-root users to use it:

`$ sudo usermod -aG i2c <username>`

If the group `i2c` doesn't exit, create it first:

`$ sudo groupadd --system i2c`

Finally, you need to install a udev rule to allow members of the group `i2c` to access to i2c devices: 

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
      Product code:         XXXXX  (0xXXXX)
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
      Product code:         XXXXX  (0xXXXX)
      Serial number:        XXXXXXXX
      Binary serial number: XXXXXXXX (0xXXXXXXXX)
      Manufacture year:     2018,  Week: 22
   VCP version:         2.1
```

### 3. Install the backend ###

### 4. Install the widget itself ###


