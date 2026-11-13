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
"""Animation definitions for Glyphy"""
import time
import tools


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
        if led_name not in self._led_objs:
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
            if led_name in self._led_objs:
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
            super().start(frequency)
            for each in self._led_objs.items():
                each[1].set_max_brightness()

        def stop(self):
            """Turn off indicated LEDs"""
            super().stop()
            for each in self._led_objs.items():
                each[1].set_off()

        def tick(self):
            """Do one tick of the animation"""


    class Blink(On):
        """Simple animation to blink LEDs"""
        def __init__(self):
            super().__init__()
            self.last_change = -1
            self.delay = -1

        def start(self, frequency=1):
            """Start blinking at set frequency"""
            # Compute delay between blinks (Equivlent to converting to seconds then dividing by 2 for delay)
            self.delay = (1 / frequency) * 1000
            self.delay = self.delay / 2
            super().start()
            self.last_change = time.time()

        def tick(self):
            """Do one tick of the animation"""
            if time.time() >= (self.last_change + self.delay):
                for each in self._led_objs.items():
                    each[1].toggle()
                self.last_change = time.time()

        def stop(self):
            """Stop blinking"""
            super().stop()
            self.last_change = -1
            self.delay = -1


    class Breath(Blink):
        """Make designated LEDs blink"""
        def __init__(self):
            """Initialize"""
            super().__init__()
            # When mode == True: increasing brightness
            # When mode == False: decreasing brightness
            # When mode == None: Off, no changes
            self.mode = True
            self.step_time = -1
            self.time_remaining_in_step = -1

        def _calc_step_size(self, max_brightness) -> int:
            # This is only ever called when self.mode is a bool
            if self.mode:
                scaler = (self.step_time - self.time_remaining_in_step) / self.step_time
            else:
                scaler = self.time_remaining_in_step / self.step_time
            return round(scaler * max_brightness)

        def start(self, frequency=0.25):
            """Start animation"""
            self.started = True
            self.delay = (1 / frequency)
            self.delay = self.delay / 2
            self.step_time = self.delay / 2
            self.time_remaining_in_step = self.delay / 2
            self.last_change = time.time()
            for each in self._led_objs.items():
                each[1].set_off()

        def tick(self):
            """Move one tick forward on the animation"""
            elapsed = time.time() - self.last_change
            self.time_remaining_in_step -= elapsed
            self.last_change = time.time()
            if self.time_remaining_in_step <= 0:
                if self.mode is True:
                    self.mode = False
                    self.time_remaining_in_step = self.delay / 2
                elif self.mode is False:
                    self.mode = None
                    self.time_remaining_in_step = self.delay
                else:
                    self.mode = True
                    self.time_remaining_in_step = self.delay / 2
            if self.mode in (True, False):
                for each in self._led_objs.items():
                    each[1].set(self._calc_step_size(each[1].max))
            else:
                for each in self._led_objs.items():
                    each[1].set_off()

        def stop(self):
            """Stop animation"""
            super().stop()
            self.time_remaining_in_step = -1
            self.step_time = -1
            for each in self._led_objs.items():
                each[1].set_off()


    class Fill(_Animate):
        """Fill Animation"""
        def __init__(self):
            """Initialize"""
            super().__init__()
            self.cell_count = 0
            self.size_per_cell = 0
            self.last_change = 0

        def start(self, frequency=0.1):
            """Start"""
            self.delay = 1 / frequency
            if len(self._led_objs) == 1:
                if "bar" in self._led_objs:
                    self.cell_count = len(self._led_objs["bar"].led_objs)
                else:
                    self.cell_count = 1
            else:
                self.cell_count = len(self._led_objs)
            self.size_per_cell = 100 / self.cell_count
            self.tick()

        def tick(self):
            """Update battery charge percentage"""
            if time.time() < (self.last_change + self.delay):
                return
            charge = tools.battery_percent()
            cells = round(charge / self.size_per_cell)
            if len(self._led_objs) == 1:
                if "bar" in self._led_objs:
                    for each in range(cells):
                        self._led_objs["bar"].led_objs[str(each)].set_max_brightness()
                else:
                    if charge == 100:
                        self._led_objs[self._led_objs.keys()[0]].set_max_brightness()
                    else:
                        self._led_objs[self._led_objs.keys()[0]].set_off()
            else:
                used = []
                for each in range(cells):
                    if ("dot" not in used) and ("dot" in self._led_objs):
                        self._led_objs["dot"].set_max_brightness()
                        used.append("dot")
                        if each == (cells - 1):
                            if "V" in self._led_objs:
                                self._led_objs["V"].set_off()
                            if "cam" in self._led_objs:
                                self._led_objs["cam"].set_off()
                            if "G" in self._led_objs:
                                self._led_objs["G"].set_off()
                            if "bar" in self._led_objs:
                                self._led_objs["bar"].set_off()
                    elif ("bar" not in used) and ("bar" in self._led_objs):
                        self._led_objs["bar"].set_max_brightness()
                        used.append("bar")
                        if each == (cells - 1):
                            if "V" in self._led_objs:
                                self._led_objs["V"].set_off()
                            if "cam" in self._led_objs:
                                self._led_objs["cam"].set_off()
                            if "G" in self._led_objs:
                                self._led_objs["G"].set_off()
                    elif ("G" not in used) and ("G" in self._led_objs):
                        self._led_objs["G"].set_max_brightness()
                        used.append("G")
                        if each == (cells - 1):
                            if "V" in self._led_objs:
                                self._led_objs["V"].set_off()
                            if "cam" in self._led_objs:
                                self._led_objs["cam"].set_off()
                    elif ("cam" not in used) and ("cam" in self._led_objs):
                        self._led_objs["cam"].set_max_brightness()
                        used.append("cam")
                        if each == (cells - 1):
                            if "V" in self._led_objs:
                                self._led_objs["V"].set_off()
                    elif ("V" not in used) and ("V" in self._led_objs):
                        self._led_objs["V"].set_max_brightness()
                        used.append("V")
            self.last_change = time.time()

        def stop(self):
            """Turn off indicated LEDs"""
            super().stop()
            for each in self._led_objs.items():
                each[1].set_off()



    class Cycle(_Animate):
        """Cycle Animation"""
        def __init__(self):
            raise NotImplementedError()

    return {"on": On,
            "blink": Blink,
            "breath": Breath,
            "fill": Fill}
