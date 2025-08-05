# POTATO  
_Power Output Translator for Analog Trigger Operations_

> ⚠️ **Proof of Concept**  
> This project is a technical prototype designed to demonstrate BLE power mapping to virtual gamepad input.  
> It is not production-ready and may require manual setup or adjustments depending on your system. 
> Consider this a dirty mostly AI-made POC! POC video: https://youtu.be/CySqMHtEQ-Q

---

## Table of Contents

1. [Description](#description)  
2. [Features](#features)  
3. [Requirements](#requirements)  
4. [Installation](#installation)  
5. [Configuration](#configuration)  
6. [Usage](#usage)  
7. [Customization](#customization)  

---

## Description

POTATO reads real-time power output from a BLE home trainer (e.g. Wahoo KICKR), maps it through a tanh curve, and feeds it into the right trigger of a virtual Xbox 360 controller.  
It optionally binds Left/Right arrow keys to the D-Pad for compatibility with tools like Zwift Play or SwiftControl.

---

## Features

- BLE scan and connection to devices matching a partial name (default: "KICKR")  
- Real-time parsing of Cycling Power Measurement (UUID `00002a63-0000-1000-8000-00805f9b34fb`)  
- Tanh-based mapping: 75% trigger at FTP, never reaches full throttle  
- Configurable FTP and power threshold via CLI  
- Virtual Xbox 360 controller output via `vgamepad`  
- Optional keyboard mapping for D-Pad (←/→)  
- Console logging of power and trigger ratio

---

## Requirements

### Hardware

- BLE-enabled home trainer supporting the Cycling Power profile  
- Windows PC with ViGEm installed (used by `vgamepad`)  
- Optional: keyboard input for D-Pad mapping

### Software

| Component      | Install Command              |
|----------------|------------------------------|
| Python ≥ 3.6   | [python.org](https://www.python.org)  
| bleak          | `pip install bleak`  
| vgamepad       | `pip install vgamepad`  
| keyboard       | `pip install keyboard`  
| ViGEm (Windows)| [vigem.org](https://vigem.org)  

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/POTATO.git

# Move into the project folder
cd POTATO

# Install Python dependencies
pip install -r requirements.txt
```

---

## Configuration

You can pass options via command line:

```bash
python potato.py --ftp 230 --device-name KICKR --threshold 20
```

Available flags:

- `--ftp` (float): Functional Threshold Power in watts (default: 230)  
- `--device-name` (str): Partial BLE device name to match (default: "KICKR")  
- `--threshold` (float): Ignore power below this value (default: 0)  
- `--disable-dpad`: Disable arrow key mapping to D-Pad

---

## Usage

Run the script:

```bash
python potato2.py
```

Once running:

- The script scans for BLE devices and connects to your trainer  
- Power notifications are received and mapped to trigger values  
- The virtual controller is updated in real time  
- Example console output:

```
Connected to KICKR  
150 W → Trigger: 0.45  
200 W → Trigger: 0.65
```

Press `Ctrl+C` to exit.

---

## Customization

- Replace the tanh curve with a linear or exponential mapping  
- Add support for other BLE characteristics (e.g. cadence, speed)  
- Use other keys or input devices to control the virtual gamepad  
