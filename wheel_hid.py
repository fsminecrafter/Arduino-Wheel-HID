#!/usr/bin/env python3

import os
import time
import json
import struct
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# ---------------- FILES ----------------

CONFIG_FILE = os.path.expanduser("~/.wheel_hid/config.json")
HID_DEVICE = "/dev/hidg0"

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

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None

def get_manual_config():
    cfg = {}
    cfg["address"] = int(input("Enter Address (hex, e.g. 0x48): "), 16)
    cfg["max"] = int(input("Enter Max: "))
    cfg["min"] = int(input("Enter Min: "))
    cfg["center"] = int(input("Enter Center: "))
    return cfg

def get_defaults():
    return {
        "address": DEFAULT_ADDRESS,
        "min": DEFAULT_MIN,
        "max": DEFAULT_MAX,
        "center": DEFAULT_CENTER,
    }

def map_range(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def main():
    # ---------- CONFIG SELECTION ----------
    cfg = None

    if ask_yn("Load config?"):
        cfg = load_config()
        if cfg is None:
            print("No config found, using defaults.")
            cfg = get_defaults()
        else:
            print("Loading config...")
            cfg = {
                "address": int(cfg["address"], 16),
                **cfg["calibration"]
            }
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

    print(f"\nUsing:")
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

            # Map with center preserved
            if raw >= adc_center:
                mapped = map_range(raw, adc_center, adc_max, 0, 32767)
            else:
                mapped = map_range(raw, adc_min, adc_center, -32767, 0)

            # Smooth
            out = last * SMOOTHING + mapped * (1.0 - SMOOTHING)
            last = out

            hid.write(struct.pack("<h", int(out)))
            time.sleep(UPDATE_DELAY)

if __name__ == "__main__":
    main()
