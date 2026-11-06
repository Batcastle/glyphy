#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  led.py
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
"""Represent individual LED states"""
import os

class LED:
    """Class to represent individual LED states"""
    def __init__(self, led_file: str, max: int, min: int):
        """Initialize LED system"""
        self.absolute_max = max
        self.max = None
        self.min = min
        self._led_file = led_file
        self.toggle = None
        self.set_max_brightness(max)

    def set_max_brightness(self, new_max: int):
        """Set the max brightness of the LEDs to brightness can be scaled if necessary"""
        if new_max > self.absolute_max:
            self.max = self.absolute_max
        elif new_max < 128:
            self.max = 128
        else:
            self.max = new_max

        def toggle(brightness=self.max):
            """Toggle current LED state"""
            if self.get() != 0:
                new = 0
            else:
                new = brightness
            self.set(new)

        self.toggle = toggle

    def reset_max_brightness(self):
        """Set the max brightness of the LEDs to brightness can be scaled if necessary"""
        self.max = self.absolute_max

        def toggle(brightness=self.max):
            """Toggle current LED state"""
            if self.get() != 0:
                new = 0
            else:
                new = brightness
            self.set(new)

        self.toggle = toggle

    def get(self) -> int:
        """Get current LED state"""
        with open(self._led_file, "r") as file:
            return int(file.read())

    def set(self, brightness: int):
        """Set current LED state"""
        with open(self._led_file, "w") as file:
            file.write(str(brightness))


class Array:
    """LED Array handler class"""
    def __init__(self, config: dict):
        """Set up LED array handler class"""
        self.led_objs = {}
        self.led_config = config["leds"]
        self.gen_config = config["general"]

        for each in self.led_config:
            if not isinstance(self.led_config[each], list):
                self.led_objs[each] = LED(f"{self.gen_config['base']}/{self.led_config[each]}", self.gen_config["max_brightness"], self.gen_config["min_brightness"])

    def get_all(self) -> dict:
        """Get the state of all LEDS in the array, represented by a dictionary"""
        output = {}
        for each in self.led_objs:
            output[each] = self.get_single(each)

    def get_single(self, name: str) -> int:
        """Get the state of a single LED in the array"""
        self.led_objs[name].get()

    def set_single(self, name: str, brightness: int):
        """Set the brightness of a single LED in the array"""
        self.led_objs[name].set(brightness)

    def set_single_max(self, name: str):
        """Set the brightness of a single LED in the array to max"""
        self.set_single(name, self.led_objs[name].max)

    def set_single_off(self, name: str):
        """Turn off a single LED in the array"""
        self.set_single(name, 0)

    def set_all_max(self):
        """Set all LEDs to max brightness"""
        # Because a different max brightness can be set for each LED, this needs to be done seperately from self.set_all()
        for each in self.led_objs:
            self.set_single(each, self.led_objs[each].max)

    def set_all_off(self):
        """Turn off all LEDs in the array"""
        self.set_all(0)

    def set_all(self, brightness: int):
        """Set brightness for all LEDs in array"""
        for each in self.led_objs:
            self.set_single(each, brightness)

    def set_max_brightness(self, new_max: int):
        """Set max brightness for array so that brightness can be scaled"""
        for each in self.led_objs:
            self.led_objs[each].set_max_brightness(new_max)

    def reset_max_brightness(self):
        """Set max brightness for array so that brightness can be scaled"""
        for each in self.led_objs:
            self.led_objs[each].reset_max_brightness()

    def list_leds(self) -> tuple:
        """Return a tuple of all valid LEDs"""
        return tuple(self.led_objs.keys())


class Glyph(led.Array):
    """Object representation for Nothing Phone 1 Glyph Lights"""
    def __init__(self, config):
        self.super(config)

        self.effects = [effect for effect in os.listdir() if "effect" in effect]
