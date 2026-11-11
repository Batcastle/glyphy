#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  tools.py
#
#  Copyright 2026 Thomas Castleman <batcastle@draugeros.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
import random
from gi.repository import Gio, GLib
import os
import hashlib


VIDEO_EXTENSIONS = (".mp4", ".m4v", ".mkv", ".webm", ".mov", ".3gp", ".avi", ".ts")
POWER_SUPPLY = "/sys/class/power_supply"


class ScreenBrightnessFollower:
    """Track the user's chosen screen brightness, ignoring dim/off."""

    def __init__(self, on_change=None):
        self.on_change = on_change  # optional; called with a float 0.0–1.0
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.dim, self.min, self.max, _default, self.ab_supported = self.bus.call_sync(
            "com.lomiri.Repowerd", "/com/lomiri/Repowerd", "com.lomiri.Repowerd",
            "getBrightnessParams", None, GLib.VariantType("((iiiib))"),
            Gio.DBusCallFlags.NONE, -1, None).unpack()[0]

        self.settings = Gio.Settings.new("com.lomiri.touch.system")
        self.settings.connect("changed::brightness", self._on_setting)
        self.settings.connect("changed::auto-brightness", self._on_setting)

        self.bus.signal_subscribe(
            "com.lomiri.Repowerd", "org.freedesktop.DBus.Properties",
            "PropertiesChanged", "/com/lomiri/Repowerd", None,
            Gio.DBusSignalFlags.NONE, self._on_repowerd)

        # GSettings only emits "changed" for keys read at least once after connecting
        self.settings.get_boolean("auto-brightness")
        self.level = None
        self._emit(self.settings.get_int("brightness"))  # seed; auto mode refines it

    def _auto(self) -> bool:
        return self.ab_supported and self.settings.get_boolean("auto-brightness")

    def _on_setting(self, settings, key):
        if not self._auto():
            self._emit(settings.get_int("brightness"))

    def _on_repowerd(self, conn, sender, path, iface, signal, params):
        interface, changed, _ = params.unpack()
        if interface != "com.lomiri.Repowerd" or "brightness" not in changed:
            return
        value = changed["brightness"]
        if not self._auto() or value in (0, self.dim):
            return  # manual mode, or the screen is dimming / turning off
        self._emit(value)

    def _emit(self, raw: int):
        level = raw / self.max
        if level != self.level:
            self.level = level
            if self.on_change is not None:
                self.on_change(level)

    def get(self) -> float:
        """Process pending brightness updates, then return the current level (0.0–1.0)."""
        context = GLib.MainContext.default()
        while context.pending():
            context.iteration(False)
        return self.level


def has_notifications() -> bool:
    """Return True if the notification drawer currently holds any notifications."""
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    try:
        result = bus.call_sync(
            "org.ayatana.indicator.messages", "/org/ayatana/indicator/messages",
            "org.gtk.Actions", "Describe", GLib.Variant("(s)", ("remove-all",)),
            GLib.VariantType("((bgav))"), Gio.DBusCallFlags.NONE, 1000, None)
    except GLib.Error:
        return False  # indicator not running or not reachable
    enabled, _param_type, _state = result.unpack()[0]
    return enabled


def enforce_brightness(led_objs: dict):
    """Ensure all LEDs are at or below their current max brightness"""
    for each in led_objs:
        if led_objs[each].get() > led_objs[each].max:
            led_objs[each].set(led_objs[each].max)


class NotificationWatcher:
    """Detect notifications arriving in the drawer between polls."""

    def __init__(self):
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self._messages = None
        self._sources = None

    def _snapshot(self):
        try:
            result = self.bus.call_sync(
                "org.ayatana.indicator.messages", "/org/ayatana/indicator/messages",
                "org.gtk.Actions", "DescribeAll", None,
                GLib.VariantType("(a{s(bgav)})"), Gio.DBusCallFlags.NONE, 1000, None)
        except GLib.Error:
            return None  # indicator not reachable
        messages = set()
        sources = {}
        for name, (_enabled, _param_type, state) in result.unpack()[0].items():
            if ".msg." in name:
                messages.add(name)
            elif ".src." in name and state:
                count, time, _string, _attention = state[0]
                sources[name] = (count, time)
        return messages, sources

    def new_notification(self) -> bool:
        """True if a notification arrived since the last call. The first call only sets a baseline."""
        snap = self._snapshot()
        if snap is None:
            return False
        messages, sources = snap
        if self._messages is None:
            self._messages, self._sources = messages, sources
            return False

        arrived = bool(messages - self._messages)
        for name, (count, time) in sources.items():
            old_count, old_time = self._sources.get(name, (0, 0))
            if count > old_count or time > old_time:
                arrived = True

        self._messages, self._sources = messages, sources
        return arrived


def gen_id(length=8) -> str:
    """Generate a unique ID for each connected device that follows these rules:
    - Arbitrary length
    - The remaining characters should be a randomly generated string of uppercase letters and numbers
    - Avoid Letters:
        - O, I
    - Avoid numnbers:
        - 0, 1
    - Have no special characters"""
    allowed_letters = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    allowed_numbers = [2, 3, 4, 5, 6, 7, 8, 9]
    suffix = []
    while length > 0:
        if (random.randint(0, 10) % 2) == 0:
            # letter
            suffix.append(random.choice(allowed_letters))
        else:
            # number
            suffix.append(str(random.choice(allowed_numbers)))
        length -= 1
    return "".join(suffix)


def _read_sysfs(path: str):
    """Read a sysfs attribute, returning None if it doesn't exist or can't be read"""
    try:
        with open(path, "r") as file:
            return file.read().strip()
    except OSError:
        return None


def _online(supply: str) -> bool:
    return _read_sysfs(f"{POWER_SUPPLY}/{supply}/online") == "1"


def battery_percent() -> float:
    """Current battery charge in percent, matching what the UI shows"""
    value = _read_sysfs(f"{POWER_SUPPLY}/battery/capacity")
    if value is None:
        raise FileNotFoundError("Could not read battery capacity")
    return float(value)


def is_wireless_charging() -> bool:
    """True if the phone is drawing power from a wireless charger"""
    return _online("dc") or _online("wireless")


def is_charging(wired_only=False) -> bool:
    """True if the phone is on external power. With wired_only=True, only USB power counts."""
    if _online("usb"):
        return True
    return False if wired_only else is_wireless_charging()


def is_recording_video() -> bool:
    """True if any process owned by this user has a video file open for writing"""
    uid = os.getuid()
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            if os.stat(f"/proc/{pid}").st_uid != uid:
                continue
            fds = os.listdir(f"/proc/{pid}/fd")
        except OSError:
            continue  # process exited, or not readable
        for fd in fds:
            try:
                target = os.readlink(f"/proc/{pid}/fd/{fd}")
            except OSError:
                continue
            if not target.lower().endswith(VIDEO_EXTENSIONS):
                continue
            try:
                with open(f"/proc/{pid}/fdinfo/{fd}") as info:
                    flags = next(int(line.split()[1], 8) for line in info if line.startswith("flags:"))
            except (OSError, ValueError, StopIteration):
                continue
            if (flags & os.O_ACCMODE) in (os.O_WRONLY, os.O_RDWR):
                return True
    return False


class FileWatcher:
    """Watch files for changes"""
    def __init__(self):
        """Initialize"""
        self.directory = "."
        self.contents = []
        self.update_contents()
        self.hashes = {}
        self.hash_contents()

    def update_contents(self) -> bool:
        """Update self.contents. Return True if there was a change."""
        try:
            contents = os.listdir(self.directory)
        except FileNotFoundError:
            self.contents = []
            return True
        if content != self.contents:
            self.contents = contents
            return True
        return False

    def hash_contents(self) -> bool:
        """Hash files in self.contents. Return True if a hash changed."""
        new_hashes = {}
        for each in self.contents:
            with open(each, 'rb') as file:
                new_hashes[each] = hashlib.file_digest(file, 'md5').hexdigest()
        changed = False
        for each in new_hashes:
            if each not in self.hashes:
                changed = True
                break
            if self.hashes[each] != new_hashes[each]:
                changed = True
                break
        self.hashes = new_hashes
        return changed
