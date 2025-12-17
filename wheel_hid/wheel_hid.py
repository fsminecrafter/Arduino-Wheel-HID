#!/usr/bin/env python3

import os
import sys
import time
import json
import struct
import argparse
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# ---------------- FILES ----------------

CONFIG_DIR = os.path.expanduser("~/.wheel_hid")
CONFIG_FILE = os.path.expanduser("~/.wheel_hid/config.json")
HID_DEVICE = "/dev/hidg0"
VENV_PY = os.path.join(CONFIG_DIR, "joystickenv", "bin", "python3")

# -------------------------------------------------
# Auto-switch to venv if present
# -------------------------------------------------
if os.path.exists(VENV_PY) and sys.executable != VENV_PY:
    os.execv(VENV_PY, [VENV_PY] + sys.argv)

# ---------------- DEFAULTS ----------------

DEFAULT_ADDRESS = 0x48
DEFAULT_MIN = 0
DEFAULT_MAX = 32767
DEFAULT_CENTER = 16384
SMOOTHING = 0.2
UPDATE_DELAY = 0.002

# ----------------------------------------

def ask_yn(prompt):
    while True:
        a = input(f"{prompt} (y/N): ").strip().lower()
        if a in ("y", "yes"):
            return True
        if a in ("", "n", "no"):
            return False

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true",
                        help="Automatically load saved config and start")
    args = parser.parse_args()

    # ---------- CONFIG SELECTION ----------
    cfg = None

    if args.auto:
        cfg_file = load_config_file()
        if not cfg_file:
            print("ERROR: --auto specified but no config found.")
            sys.exit(1)

        cfg = load_from_config(cfg_file)
        if not cfg:
            print("ERROR: Invalid config file.")
            sys.exit(1)

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

    # ---------- ADC SETUP ----------
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c, address=address)
    ads.gain = 2 / 3
    chan = AnalogIn(ads, ADS.P0)

    # ---------- HID LOOP ----------
    with open(HID_DEVICE, "wb", buffering=0) as hid:
        last = 0.0

        while True:
            raw = clamp(chan.value, adc_min, adc_max)

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
