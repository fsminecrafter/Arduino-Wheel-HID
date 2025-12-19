#!/usr/bin/env python3

import os
import sys
import time
import json
import struct
import argparse
from smbus2 import SMBus

# ---------------- FILES ----------------

CONFIG_DIR = os.path.expanduser("~/.wheel_hid")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
HID_DEVICE = "/dev/hidg0"

print(f"Config file should be at: {CONFIG_FILE}")

# ---------------- DEFAULTS ----------------

DEFAULT_ADDRESS = 0x48
DEFAULT_MIN = 0
DEFAULT_MAX = 32767
DEFAULT_CENTER = 16384
SMOOTHING = 0.2
UPDATE_DELAY = 0.002

I2C_BUS = 1
REG_CONV = 0x00
REG_CFG  = 0x01

# ----------------------------------------

def ask_yn(prompt):
    while True:
        a = input(f"{prompt} (y/N): ").strip().lower()
        if a in ("y", "yes"):
            return True
        if a in ("", "n", "no"):
            return False

def fatal(msg):
    print("\nFATAL ERROR:")
    print(msg)
    print("\nExiting.\n")
    sys.exit(1)

def load_config_file():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def get_manual_config():
    return {
        "address": int(input("Enter Address (hex, e.g. 0x48): "), 16),
        "max": int(input("Enter Max: ")),
        "min": int(input("Enter Min: ")),
        "center": int(input("Enter Center: "))
    }

def get_defaults():
    return {
        "address": DEFAULT_ADDRESS,
        "min": DEFAULT_MIN,
        "max": DEFAULT_MAX,
        "center": DEFAULT_CENTER,
    }

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def map_range(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def load_from_config(cfg):
    try:
        return {
            "address": int(cfg["address"], 16),
            "min": int(cfg["calibration"]["min"]),
            "max": int(cfg["calibration"]["max"]),
            "center": int(cfg["calibration"]["center"]),
        }
    except Exception:
        return None

# ---------- ADS1115 (SMBus) ----------

def read_ads1115(bus, addr):
    try:
        bus.write_i2c_block_data(
            addr,
            REG_CFG,
            [0xC3, 0x83]
        )
        time.sleep(0.002)

        data = bus.read_i2c_block_data(addr, REG_CONV, 2)
    except OSError as e:
        fatal(
            f"I2C ERROR while communicating with ADS1115:\n"
            f"{e}\n\n"
            "Possible causes:\n"
            " - Wrong I2C address\n"
            " - I2C not enabled or wrong overlay\n"
            " - SDA/SCL wired incorrectly\n"
            " - ADS1115 not powered\n"
            " - Loose or broken wiring"
        )

    value = (data[0] << 8) | data[1]
    if value & 0x8000:
        value -= 65536
    return value

# ----------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true",
                        help="Automatically load saved config and start")
    parser.add_argument("--test", action="store_true",
                        help="Print raw ADC value every 250ms and exit")
    args = parser.parse_args()

    # ---------- CONFIG SELECTION ----------
    cfg = None

    if args.auto:
        cfg_file = load_config_file()
        if not cfg_file:
            fatal("--auto specified but no config found.")

        cfg = load_from_config(cfg_file)
        if not cfg:
            fatal("Config file exists but is invalid or incomplete.")

        print("Auto mode: loading config...")

    else:
        if ask_yn("Load config?"):
            cfg_file = load_config_file()
            if cfg_file:
                print("Loading config...")
                cfg = load_from_config(cfg_file)
                if not cfg:
                    print("Config invalid, using defaults.")
                    cfg = get_defaults()
            else:
                print("No config found.")
                cfg = get_defaults()
        else:
            if ask_yn("OK use default values?"):
                print("Ok using default values")
                cfg = get_defaults()
            else:
                cfg = get_manual_config()

    address = cfg["address"]
    adc_min = cfg["min"]
    adc_max = cfg["max"]
    adc_center = cfg["center"]

    print("\nUsing:")
    print(f" Address : {hex(address)}")
    print(f" Min     : {adc_min}")
    print(f" Max     : {adc_max}")
    print(f" Center  : {adc_center}\n")

    # ---------- I2C OPEN ----------
    try:
        bus = SMBus(I2C_BUS)
    except FileNotFoundError:
        fatal(
            f"/dev/i2c-{I2C_BUS} not found.\n\n"
            "Possible causes:\n"
            " - I2C not enabled in armbian-config\n"
            " - Wrong I2C bus number\n"
            " - Missing device tree overlay"
        )
    except PermissionError:
        fatal(
            f"Permission denied opening /dev/i2c-{I2C_BUS}.\n\n"
            "Fix with:\n"
            " sudo usermod -aG i2c $USER\n"
            " then log out and back in"
        )

    # ---------- TEST MODE ----------
    if args.test:
        print("TEST MODE: Printing raw ADC values (Ctrl+C to exit)\n")
        try:
            while True:
                print(f"ADC raw value: {read_ads1115(bus, address)}")
                time.sleep(0.25)
        except KeyboardInterrupt:
            print("\nExited test mode.")
            sys.exit(0)

    # ---------- HID OPEN ----------
    if not os.path.exists(HID_DEVICE):
        fatal(
            f"{HID_DEVICE} does not exist.\n\n"
            "Possible causes:\n"
            " - HID gadget not created\n"
            " - Gadget not bound to USB controller\n"
            " - USB OTG cable not connected\n"
            " - libcomposite not loaded"
        )

    try:
        hid = open(HID_DEVICE, "wb", buffering=0)
    except PermissionError:
        fatal(
            f"Permission denied opening {HID_DEVICE}.\n\n"
            "Fix with:\n"
            " sudo chmod 666 /dev/hidg0\n"
            " or add a udev rule"
        )

    # ---------- HID LOOP ----------
    with hid:
        last = 0.0
        while True:
            raw = clamp(read_ads1115(bus, address), adc_min, adc_max)

            if raw >= adc_center:
                mapped = map_range(raw, adc_center, adc_max, 0, 32767)
            else:
                mapped = map_range(raw, adc_min, adc_center, -32767, 0)

            out = last * SMOOTHING + mapped * (1.0 - SMOOTHING)
            last = out

            hid.write(struct.pack("<h", int(out)))
            time.sleep(UPDATE_DELAY)

if __name__ == "__main__":
    main()
