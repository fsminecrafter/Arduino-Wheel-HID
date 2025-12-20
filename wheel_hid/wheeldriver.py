import serial
import time
import sys
import argparse

def cleanString(string):
    string = str(string)
    string = string[2:]
    string = string[:-5]
    return str(string)

def getpaircode(string):
    string = str(string)
    string = string[18:]
    string = string[:-5]
    return string

def printcleanoutput():
    print(cleanString(ser.readline()))

def valueToPercent(value: int) -> float:
    if value < -32767 or value > 32767:
        raise ValueError("Value out of range (-32767 .. 32767)")

    return (value / 32767.0) * 100.0

def remakevalue(v: int) -> int:
    # clamp input
    if v < -32767:
        v = -32767
    if v > 32767:
        v = 32767

    # map -32767..32767 → 0..32768
    return int((v + 32767) * 32768 / 65534)



if __name__ == "__main__":
    arguments = argparse.ArgumentParser()
    arguments.add_argument("--port", help="Specifies which port to use")
    arguments.add_argument("-d", "--debug", help="Outputs the incoming text from the arduino")
    args = arguments.parse_args()

    if args.port:
        port = str(args.port)
        print(f"Now using port: {port}")
    else:
        port = 'COM4'  # Default port for Windows

    if args.debug:
        with serial.Serial(port, 115200, timeout=10, rtscts=0, stopbits=1, bytesize=8) as ser:
            ser.setDTR(False)
            ser.setRTS(False)
            time.sleep(1)
            print(ser.name)
            print(cleanString(ser.readline()))
            time.sleep(5)
            code = str(ser.readline())
            code = getpaircode(code)
            print(f"Paircode found! {code}")
            ser.write(b"PAIRING_OK\r\n")
            while True:
                line = ser.readline().decode("utf-8", errors="ignore").strip()

                if not line:
                    continue

                try:
                    value = int(line)
                    print(valueToPercent(value))
                except ValueError:
                    print(f"Ignored non-numeric input: {line}")


    try:
        with serial.Serial(port, 115200, timeout=10, rtscts=0, stopbits=1, bytesize=8) as ser:
            ser.setDTR(False)
            ser.setRTS(False)
            print(f"Using: {sys.platform}")
            osplatform = sys.platform
            time.sleep(1)
            print(ser.name)
            print(cleanString(ser.readline()))
            time.sleep(5)
            code = str(ser.readline())
            code = getpaircode(code)
            print(f"Paircode found! {code}")
            ser.write(b"PAIRING_OK\r\n")
            print("Pairing Handshake done.")
            print("Calibration...")
            print("Turn the POT or WHEEL to absolute MAX")
            time.sleep(5)
            print("Turn the POT or WHEEl to minimium")
            time.sleep(5)
            print("Printing output.")
            for i in range(100):
                line = ser.readline().decode("utf-8", errors="ignore").strip()

                if not line:
                    continue

                try:
                    value = int(line)
                    print(valueToPercent(value))
                except ValueError:
                    print(f"Ignored non-numeric input: {line}")


            print("If the output was not correct restart the script.")
            time.sleep(4)
            if osplatform == "linux" or osplatform == "Linux":
                print("Starting linux virtual wheel")
                import uinput
                device = uinput.Device([
                    uinput.ABS_Y + (-32768, 32767, 0, 0)
                ], name="WheelDriver v1.0")
                print("Virtual wheel started.")
                time.sleep(3)
                while True:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    value = int(line)
                    device.emit(uinput.ABS_Y, value, syn=True)
            elif osplatform in ("win32", "Windows"):
                print("Starting windows virtual wheel (pyvjoystick)")
                from pyvjoystick import vjoy

                try:
                    wheel = vjoy.VJoyDevice(1)
                    wheel.reset()
                except Exception as e:
                    print("Failed to open vJoy device:", e)
                    sys.exit(1)

                print("Virtual wheel started.")
                time.sleep(2)

                while True:
                    try:
                        raw = ser.readline()
                        if not raw:
                            continue

                        line = raw.decode("utf-8", errors="ignore").strip()

                        # Skip non-numeric lines
                        if not line.lstrip("-").isdigit():
                            if args.debug:
                                print("IGNORED:", line)
                            continue

                        value = int(line)

                        # Map -32767..32767 → 0..32767
                        wheelvalue = remakevalue(value)
                        
                        if wheelvalue < 0:
                            wheelvalue = 0
                        elif wheelvalue > 0x8000:
                            wheelvalue = 0x8000

                        wheel.set_axis(vjoy.HID_USAGE.Y, wheelvalue)

                        print(f"RAW={value}  VJOY={wheelvalue}")

                    except Exception as e:
                        print("ERROR:", e)
                        time.sleep(0.1)

            
    except Exception as e:
        print(f"ERROR: {e}")
        ser.close()
        sys.exit(666)
        
