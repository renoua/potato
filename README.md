# POTATO  
_Power Output Translator for Analog Trigger Operations_

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]() [![PyPI](https://img.shields.io/pypi/v/potato)]()

> ⚠️ **Proof of Concept**  
> This project is a technical prototype designed to demonstrate BLE power mapping to virtual gamepad input.  
> It is not production-ready and may require manual setup or adjustments depending on your system. Consider this a dirty mostly AI-made POC!
> POC video: https://youtu.be/CySqMHtEQ-Q


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

**POTATO** reads real-time power output from a BLE home trainer (e.g., Wahoo KICKR) and maps it to an analog trigger value (0–255) on a virtual Xbox 360 controller.  
This allows you to use your pedaling power as input in games or simulations that accept gamepad controls.

---

## Features

- ✅ Automatic BLE scan and connection to devices with "KICKR" in their name  
- ⚡ Real-time parsing of Cycling Power Measurement (UUID `00002a63-0000-1000-8000-00805f9b34fb`)  
- 📈 Non-linear tanh mapping calibrated to reach 75% trigger at FTP (default: 230 W)  
- 🎮 Virtual Xbox 360 controller output via `vgamepad`  
- ⌨️ Keyboard hook for D-Pad navigation (←/→)  
- 🖥️ Console logging of power (W) and normalized trigger ratio (0.00–1.00)

---

## Requirements

### Hardware

- BLE-enabled home trainer supporting the Cycling Power profile  
- Windows PC

### Software

| Component      | Minimum Version | Install Command              |
|----------------|------------------|------------------------------|
| Python         | 3.6+             | [python.org](https://www.python.org)  
| pip            | latest           | Bundled with Python  
| bleak          | latest           | `pip install bleak`  
| vgamepad       | latest           | `pip install vgamepad`  
| keyboard       | latest           | `pip install keyboard`  

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

> 💡 On Windows, make sure vJoy is installed and configured with at least one virtual X360 device.

---

## Configuration

Open `potato.py` and adjust the following:

- `FTP_WATTS` (default: 230, my FTP) to match your personal FTP  
- The tanh mapping formula to customize sensitivity if needed (or make it linear if you want to) 
- Key bindings in `setup_keyboard_mapping()` if needed

---

## Usage

Run the script:

```bash
python potato.py
```

Once running:

- The script scans for BLE devices and connects to your KICKR  
- Power notifications are received and mapped to trigger values  
- The virtual controller is updated in real time  
- Console output example:

```
Connected to KICKR  
150 W → Trigger: 0.45  
200 W → Trigger: 0.65
```

Press `Ctrl+C` to exit.

---

## Customization

- 🔧 Replace the tanh curve with a linear or exponential mapping  
- 📡 Add support for other BLE characteristics (e.g., cadence, speed)  
- 🕹️ Swap `vgamepad` for another gamepad-emulation library if needed
