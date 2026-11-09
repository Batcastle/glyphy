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
from gi.repository import Gio, GLib


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
