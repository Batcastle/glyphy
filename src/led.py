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
        self.max = max
        self.min = min
        self._led_file = led_file

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


