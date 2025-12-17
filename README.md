# Logitech-Wheel-upgrader
This is the software for the upgrade of the Logitech gaming wheel formula with vibrations. 
This software is made for Armbian (:

![Logitech formula wheel with vibration feedback](logitechwheel.jpg)

---

This project upgrades an analog steering wheel (potentiometer-based) by using a **Le Potato** SBC as a **USB HID gaming wheel**, providing **high-resolution input** via an **ADS1115 16-bit ADC**.

The Le Potato reads the wheel position over **I²C** and exposes it to a PC as a **USB HID joystick axis** using Linux USB gadget mode.

---

## Hardware Requirements

- Le Potato (AML-S905X-CC)
- ADS1115 16-bit ADC (I²C)
- Potentiometer (steering wheel)
- USB micro-B cable (Le Potato → PC)
- PC with USB host port

---

## Software Requirements

- Armbian (recommended)
- Python 3
- Internet access (for dependency installation)

---

## How It Works

1. The potentiometer is connected to the ADS1115.
2. The ADS1115 is read over I²C.
3. The ADC value is mapped to a single joystick axis (Y axis).
4. The Le Potato presents itself as a **USB HID game controller**.
5. Games see the device as a steering wheel axis.

---

## Pre-Setup Checklist (IMPORTANT)

Before running any scripts, **all steps below must be completed**.

---

## 1. Enable I²C (Required for ADC)

I²C is required to communicate with the ADS1115.

### Enable I²C
```bash
sudo armbian-config
```
Then navigate to System → Kernel → Overlays and activate ```meson-g12a-radxa-zero-i2c-ee-m1-gpioh-6-gpioh-7```
and be careful to select the right one.
And reboot after enabling.

Verify after enabling by running `ls /dev/i2c-*`
and the expected output is `/dev/i2c-1`.
Required Kernel Modules

---

#### The following kernel modules must be available:

- libcomposite

Verify:

lsmod | grep -E "libcomposite"

#### HID Gadget Device

A USB HID gadget must be configured so this device file exists:

`/dev/hidg0`

Verify:

`ls /dev/hidg0`

<details>
If the device is not present and you havent created the HID gadget yet. please follow these instructions.
You need to have libcomposite available at this point.

  1. Enter root shell
    - Enter the shell via ```sudo -i```
  2. Go to USB gadget configfs.
    - Go to the USB gadget dir by ```cd /sys/kernel/config/usb_gadget```
  3. Create the gadget.
    ```
mkdir wheel
cd wheel
    ```
  4. Set device identity
    ```
    echo 0x1d6b > idVendor      # Linux Foundation
    echo 0x0104 > idProduct     # HID gadget
    echo 0x0100 > bcdDevice
    echo 0x0200 > bcdUSB
    ```
  5. Create USB strings
    ```
    mkdir -p strings/0x409
    echo "0001"        > strings/0x409/serialnumber
    echo "Le Potato"  > strings/0x409/manufacturer
    echo "Wheel HID"  > strings/0x409/product
    ```
  6. Create HID function
    ```
    mkdir -p functions/hid.usb0
    echo 1 > functions/hid.usb0/protocol
    echo 1 > functions/hid.usb0/subclass
    echo 2 > functions/hid.usb0/report_length
    ```
  7. HID Report Descriptor
    ```
    echo -ne \
    '\x05\x01'\
    '\x09\x04'\
    '\xA1\x01'\
    '\x09\x01'\
    '\xA1\x00'\
    '\x05\x01'\
    '\x09\x31'\
    '\x16\x01\x80'\
    '\x26\xFF\x7F'\
    '\x75\x10'\
    '\x95\x01'\
    '\x81\x02'\
    '\xC0'\
    '\xC0' \
    > functions/hid.usb0/report_desc
    ```
  8. Create configuration
    ```
    mkdir -p configs/c.1
    mkdir -p configs/c.1/strings/0x409
    echo "Wheel Config" > configs/c.1/strings/0x409/configuration
    echo 250 > configs/c.1/MaxPower
    ```
  9. Link HID function
    ```
    ln -s functions/hid.usb0 configs/c.1/
    ```
  10. Bind gadget to USB controller
    Find the controller name
    ```
    ls /sys/class/udc
    ```
    example output: fe800000.usb
    ```
    echo fe800000.usb > UDC
    ```
    Dont forget to change the example value (fe800000) to your value.
  11. Final step. Verify
    ```
    ls /dev/hidg0
    ```

Optional permissions.
`nano /etc/udev/rules.d/99-hidg.rules`
and enter this into the rule file.
`KERNEL=="hidg0", MODE="0666"`
This will make the permission mode to '666'
And dont forget to reload after saving file.
`udevadm control --reload-rules`
  
</details>

⚠️ Important
This project assumes `/dev/hidg0` already exists.
The setup script does not create the USB gadget automatically.

3. User Permissions

Run all scripts as a normal user, not root.

I²C Access
`sudo usermod -aG i2c $USER`


Log out and log back in.

HID Gadget Access (Temporary)
`sudo chmod 666 /dev/hidg0`


For permanent access, use a udev rule.

4. Install & Run Setup Script

The setup script:

- Installs dependencies
- Detects the ADS1115
- Calibrates the wheel
- Saves configuration

Run setup
`python3 setup_wheel_hid.py`


If system-wide pip installation fails:
A virtual environment named joystickenv is created automatically

- Dependencies are installed there

- Runtime scripts will use it automatically

Configuration File Location

`~/.wheel_hid/config.json?`


The config file includes:

- I²C address

- Calibration values (min / max / center)

#### Running the Wheel HID
Automatic mode (recommended)

Uses saved configuration and starts immediately.

`python3 wheel_hid.py --auto`

Manual mode

Allows interactive configuration selection.

`python3 wheel_hid.py`

USB HID Output

- Device appears as a USB game controller

- Single axis: Y axis

- 16-bit resolution

- Smoothed and centered output

- Games will detect this as a steering input.

#### Troubleshooting
`/dev/i2c-1 missing`

- I²C not enabled
- Re-check armbian-config
- Reboot
- `/dev/hidg0` missing
- USB gadget not configured
- dwc2 or libcomposite not loaded
- HID gadget setup incomplete
- Permission errors
- Confirm group membership:
  - groups
- Re-login after usermod

#### Notes

- Only one axis is exposed (ideal for steering wheels)
- Force feedback is not implemented
- Designed for low latency and high resolution
- Safe for continuous operation
