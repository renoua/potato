# POTATO  
_Power Output Translator for Analog Trigger Operations_

<!-- Badges: build | PyPI | license -->

## Table of Contents

1. [Description](#description)  
2. [Features](#features)  
3. [Requirements](#requirements)  
4. [Installation](#installation)  
5. [Configuration](#configuration)  
6. [Usage](#usage)  

---

## Description

POTATO reads real-time power output from a BLE home trainer (e.g., Wahoo KICKR) and maps it to an analog trigger value (0–255) for a virtual Xbox 360 controller via vgamepad.

---

## Features

- Automatic detection and connection to BLE cycling power devices (name includes “KICKR”).  
- Real-time parsing of cycling power measurements (UUID 00002a63-0000-1000-8000-00805f9b34fb).  
- Non-linear tanh mapping that reaches 75 % trigger at FTP (230 W).  
- Virtual Xbox 360 controller output (via vgamepad).  
- Keyboard hooks for D-Pad navigation (←/→).  
- Console logging of power (W) and normalized trigger ratio (0.00–1.00).

---

## Requirements

### Hardware

- BLE-enabled home trainer supporting the Cycling Power profile.  
- Windows PC with vJoy installed, or Linux/macOS with a virtual gamepad emulator.  
- A virtual controller configured (vJoy + vgamepad on Windows).

### Software

| Component      | Minimum Version | Installation                       |
| -------------- | --------------- | ---------------------------------- |
| Python         | 3.6+            | https://www.python.org             |
| pip            | latest          | Bundled with Python                |
| bleak          | latest          | `pip install bleak`                |
| vgamepad       | latest          | `pip install vgamepad`             |
| keyboard       | latest          | `pip install keyboard`             |
| vJoy (Windows) | 2.x             | https://github.com/shauleiz/vJoy   |

---

## Installation

1. Clone the repository  
   ```bash
   git clone https://github.com/yourusername/POTATO.git
   cd POTATO
