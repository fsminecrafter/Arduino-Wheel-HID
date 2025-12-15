#!/usr/bin/env python3

import os
import sys
import time
import json
import struct
import termios
import tty
import select
import subprocess

CONFIG_DIR = os.path.expanduser("~/.wheel_hid")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_I2C_BUS = "1"

def ask_yn(prompt):
    while True:
        ans = input(f"{prompt} (y/N): ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("", "n", "no"):
            return False

def install_dependencies():
    print("Installing dependencies...")
    subprocess.run(
        ["sudo", "apt", "update"],
        check=False
    )
    subprocess.run(
        ["sudo", "apt", "install", "-y",
         "python3-pip", "python3-smbus", "i2c-tools"],
        check=False
    )
    subprocess.run(
        ["pip3", "install", "--break-system-packages",
         "adafruit-circuitpython-ads1x15"],
        check=False
    )

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def scan_i2c():
    print("Scanning I2C bus...")
    result = subprocess.run(
        ["i2cdetect", "-y", DEFAULT_I2C_BUS],
        capture_output=True, text=True
    )
    found = []
    for line in result.stdout.splitlines():
        parts = line.split()
        for p in parts[1:]:
            if p != "--":
                try:
                    found.append(int(p, 16))
                except:
                    pass
    return found

def find_ads1115():
    print("Set the pot to MAX...")
    time.sleep(2)
    addrs = scan_i2c()
    if not addrs:
        print("Could not be found")
        print("Set the pot to MIN in 5 seconds. Please double check.")
        time.sleep(5)
        addrs = scan_i2c()
        if not addrs:
            print("Could not be found")
            return None
    return addrs[0]

def read_adc(addr):
    import board, busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn

    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c, address=addr)
    ads.gain = 2/3
    chan = AnalogIn(ads, ADS.P0)
    return chan.value

def wait_keypress():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        r, _, _ = select.select([sys.stdin], [], [])
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def calibration(addr):
    cal = {}

    input("Set the pot to MAX, then press Enter.")
    cal["max"] = read_adc(addr)
    print("OK!")

    input("Set the pot to MIN, then press Enter.")
    cal["min"] = read_adc(addr)
    print("OK!")

    input("Set the pot to MIDDLE, then press Enter.")
    cal["center"] = read_adc(addr)
    print("OK!")

    print("Try sensor, Exit with Backspace.")
    while True:
        val = read_adc(addr)
        print(val)
        time.sleep(0.1)
        if select.select([sys.stdin], [], [], 0)[0]:
            ch = wait_keypress()
            if ch == "\x08" or ch == "\x7f":
                print("Exited...")
                break

    return cal

def main():
    print("Have you enabled I2C?")
    if not ask_yn(""):
        print("Please enable I2C via armbian-config and reboot.")
        sys.exit(1)

    install_dependencies()

    cfg = load_config()

    if "address" in cfg and ask_yn("Do you want to load the saved address for the sensor?"):
        addr = int(cfg["address"], 16)
        print(f"Loading address from save...\nSetting address to: {hex(addr)}")
    else:
        if ask_yn("Do you know the address for the sensor?"):
            addr = int(input("Enter address (hex, e.g. 0x48): "), 16)
        else:
            while True:
                addr = find_ads1115()
                if addr is not None:
                    print(f"Address found!\nSetting address to: {hex(addr)}")
                    break
                if not ask_yn("Retry?"):
                    sys.exit(1)

        if ask_yn("Save address for later?"):
            cfg["address"] = hex(addr)
            save_config(cfg)
            print("Saving...\nSaved.")

    if ask_yn("Start calibration?"):
        cal = calibration(addr)
        if ask_yn("Do you want to save calibration?"):
            cfg["calibration"] = cal
            cfg["address"] = hex(addr)
            save_config(cfg)
            print("OK saving...\nSaved...")
        else:
            print("Ok, exiting...")
    else:
        print("The setup is done and is being exited.")

    print("Exiting...")

if __name__ == "__main__":
    main()
