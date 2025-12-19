Arduino-Wheel-HID
=================

This project allows you to turn a **potentiometer-based analog wheel** into a **USB HID gaming wheel** using an **Arduino UNO**, sending data to a PC for games to recognize.

It works cross-platform on **Windows** (vJoy) and **Linux** (uinput) and supports automatic pairing, connection monitoring, and smoothed 16-bit input.

⚠️ Important
------------

This project is designed for **Arduino UNO**. Other boards may work but require modifications.

Hardware Requirements
---------------------

*   Arduino UNO (or compatible)
    
*   ADS1115 16-bit ADC (I²C)
    
*   Potentiometer (steering wheel)
    
*   USB cable (Arduino → PC)
    
*   PC with USB host
    

Software Requirements
---------------------

*   Python 3
    
*   pyserial
    
*   pyvjoy (Windows) or python-uinput (Linux)
    
*   Internet access for dependencies
    

How It Works
------------

1.  Potentiometer connects to ADS1115.
    
2.  Arduino reads ADS1115 over I²C.
    
3.  Arduino maps raw ADC value to a 16-bit axis.
    
4.  Arduino sends data over **serial** to the PC.
    
5.  PC receives data and exposes it as a **joystick axis**:
    
    *   Windows → vJoy
        
    *   Linux → uinput
        
6.  Games detect this as a steering wheel axis.
    

Features
--------

*   Automatic pairing with PC via **pairing code**.
    
*   Connection monitoring: returns to pairing if serial is lost.
    
*   Smoothed, high-resolution 16-bit axis.
    
*   Fast updates (~100Hz).
    
*   Works on Windows and Linux without modifying the Arduino hardware.
    
*   Single axis (ideal for steering wheel projects).
    

Setup Instructions
------------------

### 1\. Connect Hardware

*   ADS1115 → Arduino (I²C)
    
*   Potentiometer → ADS1115 channel A0
    
*   Ensure proper power and ground connections.
    

### 2\. Upload Arduino Sketch

*   Use Arduino IDE to upload wheel\_hid.ino.
    
*   Ensure serial monitor is closed when running the PC script.
    

### 3\. Install Dependencies on PC

`   pip3 install pyserial  # Windows only:  pip3 install pyvjoy  # Linux only:  pip3 install python-uinput   `

### 4\. Run Python HID Script

#### Automatic mode (recommended)

Uses saved configuration and starts immediately:

`   python3 wheel_hid_pc.py --auto   `

#### Manual mode

Allows interactive pairing and calibration:

`   python3 wheel_hid_pc.py   `

### 5\. Pairing

*   Arduino sends a **pairing request** on serial.
    
*   PC must respond with the **pairing code**.
    
*   Once paired, data will stream automatically.
    
*   If the connection is lost, PC re-enters pairing mode.
    

### 6\. Axis Mapping & Smoothing

*   Raw ADC values are dynamically mapped to -32767..32767.
    
*   Smoothed output reduces jitter.
    
*   Mapped value is sent to vJoy or uinput axis for gaming.
    

Troubleshooting
---------------

*   Serial connection errors → check cable and port.
    
*   Invalid values → check potentiometer wiring.
    
*   Windows vJoy errors → ensure vJoy driver is installed and configured.
    
*   Linux uinput errors → ensure user has permission (sudo modprobe uinput and group membership).
    
*   Arduino sketch not responding → power-cycle Arduino.
    

### Notes

*   Only one axis exposed (steering wheel).
    
*   High resolution for smooth input.
    
*   Low latency.
    
*   Force feedback not implemented.
    
*   Safe for continuous use.
