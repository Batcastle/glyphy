#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  animations.py
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
import time
import os


class _Animate:
    """Define Standard ABI for Animations

    THIS CLASS IS SIMPLY THE STANDARD ALL SOFTWARE ANIMATIONS FOLLOW! DO NOT USE AS ANIMATION!
    """
    def __init__(self):
        """Create any variables you need, such as time stamps, length variables, etc"""
        self._led_objs = {}
        self.started = False

    def add_led(self, led_name: str, led_obj):
        """Add new LED file"""
        if led_name not in self._led_objs.keys():
            self._led_objs[led_name] = led_obj

    def start(self, _):
        """Start animation"""
        self.started = True

    def tick(self):
        """Do one tick of the animation"""
        raise NotImplementedError()

    def stop(self):
        """Stop animations"""
        self.started = False

    def remove_led(self, led_name: str):
        """Remove LED files"""
        if not self.started:
            if led_name in self._led_objs.keys():
                    del self._led_objs[led_name]
        else:
            raise RuntimeError("Cannot edit LED list while animation is running. Stop animation with the stop() method first.")

    def remove_all_leds(self):
        """Remove ALL LED files"""
        if not self.started:
            keys = self._led_objs.keys()
            for each in keys:
                del self._led_objs[each]
        else:
            raise RuntimeError("Cannot edit LED list while animation is running. Stop animation with the stop() method first.")


def init() -> dict:
    """Initialize software animation classes and return a dictionary containing uninitialized animation objects"""
    class On(_Animate):
        """Simple animation, turns LED on"""

        def start(self, frequency=None):
            """Turn on indicated LEDs"""
            super(On, self).start(frequency)
            for each in self._led_objs:
                self._led_objs[each].set_max_brightness()

        def stop(self):
            """Turn off indicated LEDs"""
            super(On, self).stop()
            for each in self._led_objs:
                self._led_objs[each].set_off()

        def tick(self):
            """Do one tick of the animation"""
            pass


    class Blink(On):
        """Simple animation to blink LEDs"""
        def __init__(self):
            super(Blink, self).__init__()
            self.last_change = -1
            self.delay = -1

        def start(self, frequency=1):
            """Start blinking at set frequency"""
            # Compute delay between blinks
            self.delay = frequency / 2
            super(Blink, self).start()
            self.last_change = time.time()

        def tick(self):
            """Do one tick of the animation"""
            if time.time() >= (self.last_change + self.delay):
                for each in self._led_objs:
                    self._led_objs[each].toggle()
                self.last_change = time.time()

        def stop(self):
            """Stop blinking"""
            super(Blink, self).stop()
            self.last_change = -1
            self.delay = -1


    class Breath(On):
        def __init__(self):
            raise NotImplementedError()


    class Fill(On):
        def __init__(self):
            raise NotImplementedError()

    return {"On": On,
            "Blink": Blink}
