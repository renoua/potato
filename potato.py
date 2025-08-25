#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
POTATO POC

Reads cycling power from a BLE home trainer (e.g. Wahoo KICKR),
maps it through a tanh curve, and feeds it into the right trigger of
a virtual Xbox 360 controller. Optionally binds Left/Right arrow keys
to the D-pad (for compatibility with Zwift Play) and/or displays a GUI.
"""

# Standard lib
import asyncio
import threading
import math
import argparse
import tkinter as tk

# Third-party
import keyboard      # pip install keyboard
import vgamepad      # pip install vgamepad
from vgamepad import XUSB_BUTTON
from bleak import BleakClient, BleakScanner

# UUID for the BLE Cycling Power Measurement characteristic
CPM_UUID = "00002a63-0000-1000-8000-00805f9b34fb"


def parse_cycling_power(data: bytearray) -> int:
    """
    Extract instantaneous power (in watts) from the raw Cycling Power Measurement packet.
    Format (little‐endian, signed) at bytes 2–3.

    :param data: bytearray from BLE notification
    :return: signed integer power in watts, or 0 if packet is too short
    """
    if len(data) < 4:
        return 0
    return int.from_bytes(data[2:4], byteorder='little', signed=True)


class KickrController:
    """
    Manages BLE connection to the KICKR, receives power notifications,
    applies a tanh-based mapping, and updates a virtual gamepad.
    """

    def __init__(self, ftp, device_name, threshold, update_callback):
        """
        :param ftp: functional threshold power (used for tanh scaling)
        :param device_name: BLE name (partial match) of the trainer
        :param threshold: minimum power (watts) required to engage throttle
        :param update_callback: function(power_watts: int, trigger_ratio: float)
        """
        self.ftp = ftp
        self.device_name = device_name.upper()
        self.threshold = threshold
        self.client = None
        self.power = 0
        self.trigger = 0.0
        self.update_callback = update_callback
        self.gamepad = vgamepad.VX360Gamepad()

    async def connect(self) -> bool:
        """
        Scan for BLE devices, find one whose name matches, and attempt to connect.
        """
        print("Scanning for BLE devices...")
        try:
            devices = await asyncio.wait_for(BleakScanner.discover(), timeout=10)
        except asyncio.TimeoutError:
            print("Scan timed out.")
            return False

        device = next(
            (d for d in devices if d.name and self.device_name in d.name.upper()),
            None
        )

        if not device:
            print(f"No device named '{self.device_name}' found.")
            return False

        print(f"Found {device.name} @ {device.address}. Connecting…")
        self.client = BleakClient(device.address)

        try:
            await self.client.connect()
            print(f"Connected to {device.name}")
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    async def handle_power_notify(self, sender, data: bytearray):
        """
        Callback invoked on each power notification.
        Parses power, computes trigger ratio, and updates the virtual gamepad.

        :param sender: BLE characteristic UUID (unused)
        :param data: raw notification bytes
        """
        self.power = parse_cycling_power(data)

        # Ignore values below threshold
        if self.power < self.threshold:
            self.trigger = 0.0
        else:
            # Map using tanh: at ftp watts → ~75% trigger
            scale = math.atanh(0.75) / self.ftp
            self.trigger = math.tanh(scale * self.power)

        # Convert 0.0–1.0 ratio to 0–255 trigger byte
        trigger_value = int(self.trigger * 255)

        # Update virtual controller
        self.gamepad.right_trigger(trigger_value)
        self.gamepad.update()

        # Optional callback for debug or UI
        self.update_callback(self.power, self.trigger)

    async def start_notifications(self):
        """
        Subscribe to BLE power notifications.
        """
        try:
            await self.client.start_notify(CPM_UUID, self.handle_power_notify)
            print("Started power notifications.")
        except Exception as e:
            print(f"Failed to start notifications: {e}")

    async def run(self):
        """
        Full lifecycle: connect → subscribe → stay alive.
        """
        if not await self.connect():
            return
        await self.start_notifications()
        while True:
            await asyncio.sleep(1)


def setup_keyboard_mapping(gamepad: vgamepad.VX360Gamepad):
    """Bind Zwift Play and extra keyboard keys to gamepad buttons."""
    key_map = {
        # Zwift Play main buttons
        "left": XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
        "right": XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        "home": XUSB_BUTTON.XUSB_GAMEPAD_A,                  # Home → A
        "shift": XUSB_BUTTON.XUSB_GAMEPAD_B,                 # Shift Left → B
        "enter": XUSB_BUTTON.XUSB_GAMEPAD_X,                 # Enter → X
        "end": XUSB_BUTTON.XUSB_GAMEPAD_Y,                   # End → Y
        "=": XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,        # = → R1
        "subtract": XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER      # Numpad - → L1
    }

    for key, btn in key_map.items():
        keyboard.on_press_key(key, lambda e, b=btn: (
            gamepad.press_button(b),
            gamepad.update()
        ))
        keyboard.on_release_key(key, lambda e, b=btn: (
            gamepad.release_button(b),
            gamepad.update()
        ))

class MinimalGUI:
    """
    Minimalist Tkinter window to display watts inside a horizontal bar.
    Perfect for OBS overlay.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Power Bar")
        self.root.configure(bg="black")
        self.root.geometry("300x50")
        self.root.resizable(False, False)

        # Canvas for bar and text
        self.canvas = tk.Canvas(self.root, height=30, width=280, bg="black", highlightthickness=0)
        self.canvas.pack(pady=10)

        # Background rectangle
        self.canvas.create_rectangle(0, 0, 280, 30, outline="white", fill="black", tags="bg")

        # Foreground rectangle (progress)
        self.canvas.create_rectangle(0, 0, 0, 30, outline="", fill="lime", tags="bar")

        # Watts text in the center
        self.canvas.create_text(140, 15, text="0 W", fill="white",
                                font=("Helvetica", 14, "bold"), tags="text")

    def update(self, power, trigger):
        """
        Update bar length and watts text.
        """
        bar_length = int(trigger * 280)
        self.canvas.coords("bar", 0, 0, bar_length, 30)
        self.canvas.itemconfig("text", text=f"{power} W")

    def run(self):
        self.root.mainloop()


def start_loop(loop: asyncio.AbstractEventLoop):
    """
    Dedicated thread event loop for BLE.
    """
    asyncio.set_event_loop(loop)
    loop.run_forever()


def main():
    """
    Entry point: parse CLI, start BLE, map keyboard, and optionally show GUI.
    """
    parser = argparse.ArgumentParser(description="BLE to Gamepad bridge")
    parser.add_argument("--ftp", type=float, default=230.0,
                        help="Functional Threshold Power in watts")
    parser.add_argument("--device-name", type=str, default="KICKR",
                        help="Partial name of BLE device (e.g. KICKR)")
    parser.add_argument("--threshold", type=float, default=0,
                        help="Ignore power below this wattage")
    parser.add_argument("--disable-dpad", action="store_true",
                        help="Disable arrow key mapping to D-Pad")
    parser.add_argument("--gui", action="store_true",
                        help="Show minimal GUI for power and trigger")
    args = parser.parse_args()

    # GUI setup if enabled
    gui = MinimalGUI() if args.gui else None

    # New thread & loop for BLE
    loop = asyncio.new_event_loop()
    threading.Thread(target=start_loop, args=(loop,), daemon=True).start()

    controller = KickrController(
        ftp=args.ftp,
        device_name=args.device_name,
        threshold=args.threshold,
        update_callback=(gui.update if gui else
                         lambda p, t: print(f"{p} W → Trigger: {t:.2f}"))
    )

    # Keyboard mapping (optional)
    if not args.disable_dpad:
        setup_keyboard_mapping(controller.gamepad)

    asyncio.run_coroutine_threadsafe(controller.run(), loop)

    # Start GUI or wait for keyboard
    if gui:
        gui.run()
    else:
        keyboard.wait()


if __name__ == "__main__":
    main()
