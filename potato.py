#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
POTATO POC

This proof‐of‐concept reads cycling power from a BLE home trainer (e.g. Wahoo KICKR),
maps it through a tanh curve, and feeds it into the right trigger of a virtual
Xbox 360 controller. It also hooks Left/Right arrow keys to the D‐pad.
"""

import asyncio
import threading
import math        # We use math.tanh for non‐linear mapping
import time

import keyboard    # pip install keyboard
import vgamepad    # pip install vgamepad
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
    # Bytes 2–3 hold the “Instantaneous Power” field
    return int.from_bytes(data[2:4], byteorder='little', signed=True)


class KickrController:
    """
    Manages BLE connection to the KICKR, receives power notifications,
    applies a tanh-based mapping, and updates a virtual gamepad.
    """

    def __init__(self, update_callback):
        """
        :param update_callback: function(power_watts: int, trigger_ratio: float)
                                called on each power update, e.g. for console logging
        """
        self.client = None
        self.power = 0
        self.trigger = 0.0
        self.update_callback = update_callback
        # Instantiate a virtual Xbox 360 controller
        self.gamepad = vgamepad.VX360Gamepad()

    async def connect(self) -> bool:
        """
        Scan for BLE devices, find one whose name contains “KICKR”,
        and attempt to connect.

        :return: True on success, False otherwise
        """
        print("Scanning for BLE devices...")
        devices = await BleakScanner.discover()
        # Filter for any device with “KICKR” in its name (case‐insensitive)
        kickr = next((d for d in devices if d.name and "KICKR" in d.name.upper()), None)

        if not kickr:
            print("No KICKR device found.")
            return False

        print(f"Found {kickr.name} @ {kickr.address}. Connecting…")
        self.client = BleakClient(kickr.address)

        try:
            await self.client.connect()
            print(f"Connected to {kickr.name}")
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    async def handle_power_notify(self, sender, data: bytearray):
        """
        Callback invoked on each power notification.
        Parses power, computes trigger ratio, and updates the virtual gamepad.

        :param sender: handle/UUID of the characteristic (unused)
        :param data: raw notification bytearray
        """
        # 1. Parse instantaneous power (watts)
        self.power = parse_cycling_power(data)

        # 2. Apply a tanh curve to make it easy to reach 75% of throttle but impossible to reach 100%:
        #    - at FTP_WATTS=230W, tanh → 0.75
        #    - ratio = tanh((atanh(0.75)/FTP) * current_power)
        ftp_watts = 230.0
        scale = math.atanh(0.75) / ftp_watts
        self.trigger = math.tanh(scale * self.power)

        # 3. Convert ratio (0.0–1.0) → trigger byte (0–255)
        trigger_value = int(self.trigger * 255)

        # 4. Update the virtual controller
        self.gamepad.right_trigger(trigger_value)
        self.gamepad.update()

        # 5. Call user‐supplied callback (e.g. for print/log)
        self.update_callback(self.power, self.trigger)

    async def start_notifications(self):
        """
        Subscribe to power measurement notifications.
        """
        try:
            await self.client.start_notify(CPM_UUID, self.handle_power_notify)
            print("Started power notifications.")
        except Exception as e:
            print(f"Failed to start notifications: {e}")

    async def run(self):
        """
        Full lifecycle: connect → subscribe → keep the loop alive.
        """
        if not await self.connect():
            return
        await self.start_notifications()
        # Keep the coroutine alive to keep receiving notifications
        while True:
            await asyncio.sleep(1)


def setup_keyboard_mapping(gamepad: vgamepad.VX360Gamepad):
    """
    Bind the left/right arrow keys to D-Pad presses on the virtual controller.
    This works with Zwift Play and https://github.com/renoua/swiftcontrol.
    """
    # D-Pad Left
    keyboard.on_press_key("left", lambda e: (
        gamepad.press_button(XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
        gamepad.update()
    ))
    keyboard.on_release_key("left", lambda e: (
        gamepad.release_button(XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
        gamepad.update()
    ))

    # D-Pad Right
    keyboard.on_press_key("right", lambda e: (
        gamepad.press_button(XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
        gamepad.update()
    ))
    keyboard.on_release_key("right", lambda e: (
        gamepad.release_button(XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
        gamepad.update()
    ))


def start_loop(loop: asyncio.AbstractEventLoop):
    """
    Worker target: set up the event loop for BLE notifications in this thread.
    """
    asyncio.set_event_loop(loop)
    loop.run_forever()


def main():
    """
    Entry point:
      1. Create and start a background thread for asyncio BLE tasks.
      2. Instantiate the KickrController with a print callback.
      3. Hook keyboard arrows to D‐pad.
      4. Schedule the BLE run() coroutine.
      5. Block on keyboard.wait() so the script stays alive.
    """
    # 1) New event loop in a daemon thread for BLE
    loop = asyncio.new_event_loop()
    threading.Thread(target=start_loop, args=(loop,), daemon=True).start()

    # 2) Kickr controller instance
    controller = KickrController(update_callback=lambda p, t: print(f"{p} W → Trigger: {t:.2f}"))

    # 3) Keyboard hooks → D‐pad mapping
    setup_keyboard_mapping(controller.gamepad)

    # 4) Schedule BLE run() on the new loop
    asyncio.run_coroutine_threadsafe(controller.run(), loop)

    # 5) Block here so our main thread doesn’t exit (Ctrl+C to quit)
    keyboard.wait()


if __name__ == "__main__":
    main()
