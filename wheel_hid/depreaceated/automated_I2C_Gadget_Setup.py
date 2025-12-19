#!/usr/bin/env python3

# Made for Le potato (AML-S905X-CC) Using armbian

import os
import sys
import subprocess
import time
import shutil

GADGET_DIR = "/sys/kernel/config/usb_gadget"
GADGET_NAME = "wheel"
GADGET_PATH = os.path.join(GADGET_DIR, GADGET_NAME)
UDEV_RULE = "/etc/udev/rules.d/99-hidg.rules"

def run(cmd, check=True):
    print(f"> {cmd}")
    subprocess.run(cmd, shell=True, check=check)

def require_root():
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root.")
        print("Run with: sudo python3 automated_I2C_Gadget_Setup.py")
        sys.exit(1)

def header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")

def check_i2c():
    header("Checking I2C support")
    if not os.path.exists("/dev/i2c-1"):
        print("WARNING: /dev/i2c-1 not found.")
        print("Make sure I2C is enabled via armbian-config.")
    else:
        print("I2C device found: /dev/i2c-1")

def check_libcomposite():
    header("Checking libcomposite")
    try:
        run("modprobe libcomposite")
        print("libcomposite loaded")
    except subprocess.CalledProcessError:
        print("ERROR: libcomposite not available.")
        sys.exit(1)

def remove_existing_gadget():
    header("Removing existing HID gadget (if any)")

    if not os.path.exists(GADGET_PATH):
        print("No existing gadget found.")
        return

    try:
        if os.path.exists(f"{GADGET_PATH}/UDC"):
            run(f"echo '' > {GADGET_PATH}/UDC", check=False)

        for root, dirs, files in os.walk(GADGET_PATH, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        os.rmdir(GADGET_PATH)
        print("Old gadget removed.")
    except Exception as e:
        print("ERROR removing old gadget:", e)
        sys.exit(1)

def create_gadget():
    header("Creating HID Wheel Gadget")

    run(f"mkdir {GADGET_PATH}")
    os.chdir(GADGET_PATH)

    # Device identity
    run("echo 0x1d6b > idVendor")
    run("echo 0x0104 > idProduct")
    run("echo 0x0100 > bcdDevice")
    run("echo 0x0200 > bcdUSB")

    # Strings
    run("mkdir -p strings/0x409")
    run("echo '0001' > strings/0x409/serialnumber")
    run("echo 'Le Potato' > strings/0x409/manufacturer")
    run("echo 'Wheel HID' > strings/0x409/product")

    # HID function
    run("mkdir -p functions/hid.usb0")
    run("echo 1 > functions/hid.usb0/protocol")
    run("echo 1 > functions/hid.usb0/subclass")
    run("echo 2 > functions/hid.usb0/report_length")

    # HID report descriptor (16-bit signed Y axis)
    run(
        "echo -ne "
        "'\\x05\\x01'"
        "'\\x09\\x04'"
        "'\\xA1\\x01'"
        "'\\x09\\x01'"
        "'\\xA1\\x00'"
        "'\\x05\\x01'"
        "'\\x09\\x31'"
        "'\\x16\\x01\\x80'"
        "'\\x26\\xFF\\x7F'"
        "'\\x75\\x10'"
        "'\\x95\\x01'"
        "'\\x81\\x02'"
        "'\\xC0'"
        "'\\xC0' "
        "> functions/hid.usb0/report_desc"
    )

    # Config
    run("mkdir -p configs/c.1/strings/0x409")
    run("echo 'Wheel Config' > configs/c.1/strings/0x409/configuration")
    run("echo 250 > configs/c.1/MaxPower")

    # Link function
    run("ln -s functions/hid.usb0 configs/c.1/")

def bind_gadget():
    header("Binding gadget to USB controller")

    udc_list = os.listdir("/sys/class/udc")
    if not udc_list:
        print("ERROR: No USB UDC found.")
        sys.exit(1)

    udc = udc_list[0]
    print(f"Using UDC: {udc}")
    run(f"echo {udc} > {GADGET_PATH}/UDC")

def setup_udev():
    header("Optional: HID permissions")

    choice = input("Install udev rule for /dev/hidg0? (y/N): ").strip().lower()
    if choice not in ("y", "yes"):
        return

    with open(UDEV_RULE, "w") as f:
        f.write('KERNEL=="hidg0", MODE="0666"\n')

    run("udevadm control --reload-rules")
    run("udevadm trigger")
    print("udev rule installed.")

def verify():
    header("Verification")

    if os.path.exists("/dev/hidg0"):
        print("SUCCESS: /dev/hidg0 exists")
    else:
        print("ERROR: /dev/hidg0 not found")

def main():
    require_root()

    header("Automated I2C + HID Gadget Setup (Le Potato)")

    print("This script will:")
    print("- Verify I2C")
    print("- Load libcomposite")
    print("- Remove any existing HID gadget")
    print("- Create a Wheel HID gadget")
    print("- Bind it to USB OTG")
    print("- Optionally set permissions\n")

    input("Press Enter to continue or Ctrl+C to abort...")

    check_i2c()
    check_libcomposite()
    remove_existing_gadget()
    create_gadget()
    bind_gadget()
    setup_udev()
    verify()

    print("\nSetup complete.")
    print("You can now run wheel_hid.py")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3

import os
import sys
import subprocess
import time
import shutil

GADGET_DIR = "/sys/kernel/config/usb_gadget"
GADGET_NAME = "wheel"
GADGET_PATH = os.path.join(GADGET_DIR, GADGET_NAME)
UDEV_RULE = "/etc/udev/rules.d/99-hidg.rules"

def run(cmd, check=True):
    print(f"> {cmd}")
    subprocess.run(cmd, shell=True, check=check)

def require_root():
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root.")
        print("Run with: sudo python3 automated_I2C_Gadget_Setup.py")
        sys.exit(1)

def header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")

def check_i2c():
    header("Checking I2C support")
    if not os.path.exists("/dev/i2c-1"):
        print("WARNING: /dev/i2c-1 not found.")
        print("Make sure I2C is enabled via armbian-config.")
    else:
        print("I2C device found: /dev/i2c-1")

def check_libcomposite():
    header("Checking libcomposite")
    try:
        run("modprobe libcomposite")
        print("libcomposite loaded")
    except subprocess.CalledProcessError:
        print("ERROR: libcomposite not available.")
        sys.exit(1)

def remove_existing_gadget():
    header("Removing existing HID gadget (if any)")

    if not os.path.exists(GADGET_PATH):
        print("No existing gadget found.")
        return

    try:
        if os.path.exists(f"{GADGET_PATH}/UDC"):
            run(f"echo '' > {GADGET_PATH}/UDC", check=False)

        for root, dirs, files in os.walk(GADGET_PATH, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        os.rmdir(GADGET_PATH)
        print("Old gadget removed.")
    except Exception as e:
        print("ERROR removing old gadget:", e)
        sys.exit(1)

def create_gadget():
    header("Creating HID Wheel Gadget")

    run(f"mkdir {GADGET_PATH}")
    os.chdir(GADGET_PATH)

    # Device identity
    run("echo 0x1d6b > idVendor")
    run("echo 0x0104 > idProduct")
    run("echo 0x0100 > bcdDevice")
    run("echo 0x0200 > bcdUSB")

    # Strings
    run("mkdir -p strings/0x409")
    run("echo '0001' > strings/0x409/serialnumber")
    run("echo 'Le Potato' > strings/0x409/manufacturer")
    run("echo 'Wheel HID' > strings/0x409/product")

    # HID function
    run("mkdir -p functions/hid.usb0")
    run("echo 1 > functions/hid.usb0/protocol")
    run("echo 1 > functions/hid.usb0/subclass")
    run("echo 2 > functions/hid.usb0/report_length")

    # HID report descriptor (16-bit signed Y axis)
    run(
        "echo -ne "
        "'\\x05\\x01'"
        "'\\x09\\x04'"
        "'\\xA1\\x01'"
        "'\\x09\\x01'"
        "'\\xA1\\x00'"
        "'\\x05\\x01'"
        "'\\x09\\x31'"
        "'\\x16\\x01\\x80'"
        "'\\x26\\xFF\\x7F'"
        "'\\x75\\x10'"
        "'\\x95\\x01'"
        "'\\x81\\x02'"
        "'\\xC0'"
        "'\\xC0' "
        "> functions/hid.usb0/report_desc"
    )

    # Config
    run("mkdir -p configs/c.1/strings/0x409")
    run("echo 'Wheel Config' > configs/c.1/strings/0x409/configuration")
    run("echo 250 > configs/c.1/MaxPower")

    # Link function
    run("ln -s functions/hid.usb0 configs/c.1/")

def bind_gadget():
    header("Binding gadget to USB controller")

    udc_list = os.listdir("/sys/class/udc")
    if not udc_list:
        print("ERROR: No USB UDC found.")
        sys.exit(1)

    udc = udc_list[0]
    print(f"Using UDC: {udc}")
    run(f"echo {udc} > {GADGET_PATH}/UDC")

def setup_udev():
    header("Optional: HID permissions")

    choice = input("Install udev rule for /dev/hidg0? (y/N): ").strip().lower()
    if choice not in ("y", "yes"):
        return

    with open(UDEV_RULE, "w") as f:
        f.write('KERNEL=="hidg0", MODE="0666"\n')

    run("udevadm control --reload-rules")
    run("udevadm trigger")
    print("udev rule installed.")

def verify():
    header("Verification")

    if os.path.exists("/dev/hidg0"):
        print("SUCCESS: /dev/hidg0 exists")
    else:
        print("ERROR: /dev/hidg0 not found")

def main():
    require_root()

    header("Automated I2C + HID Gadget Setup (Le Potato)")

    print("This script will:")
    print("- Verify I2C")
    print("- Load libcomposite")
    print("- Remove any existing HID gadget")
    print("- Create a Wheel HID gadget")
    print("- Bind it to USB OTG")
    print("- Optionally set permissions\n")

    input("Press Enter to continue or Ctrl+C to abort...")

    check_i2c()
    check_libcomposite()
    remove_existing_gadget()
    create_gadget()
    bind_gadget()
    setup_udev()
    verify()

    print("\nSetup complete.")
    print("You can now run wheel_hid.py")

if __name__ == "__main__":
    main()
