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
import time
import animations
import tools


class LED:
    """Class to represent individual LED states"""
    def __init__(self, led_file: str, max: int, min: int, single_mode=False, single=None):
        """Initialize LED system"""
        self.absolute_max = max
        self.max = None
        self.min = min
        self.brightness = 0
        self._led_file = led_file
        self.toggle = None
        self.change_max_brightness(max)
        self.single_mode = single_mode
        self.single = single

    def change_max_brightness(self, new_max: int):
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
            self.brightness = new

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
            self.brightness = new

        self.toggle = toggle

    def get(self) -> int:
        """Get current LED state"""
        if not self.single_mode:
            with open(self._led_file, "r") as file:
                return int(file.read())
        else:
            return self.brightness

    def set(self, brightness: int):
        """Set current LED state"""
        if self.single_mode:
            with open(self._led_file, "w") as file:
                file.write(f"{self.single} {brightness}")
        else:
            with open(self._led_file, "w") as file:
                file.write(str(brightness))
        self.brightness = brightness

    def set_max_brightness(self):
        """Set LED to max brightness"""
        self.set(self.max)

    def set_off(self):
        """Turn LED off"""
        self.set(0)


class Array:
    """LED Array handler class"""
    def __init__(self, config: dict):
        """Set up LED array handler class"""
        self.led_objs = {}
        self.led_config = config["leds"]
        self.gen_config = config["general"]

        for each in self.led_config:
            if isinstance(self.led_config[each], dict):
                new_config = {"general": self.gen_config,
                              "leds": self.led_config[each]}
                new_config["leds"]["single"] = self.led_config["single"]
                self.led_objs[each] = Array(new_config)
            elif isinstance(self.led_config[each], int):
                self.led_objs[each] = LED(f"{self.gen_config['base']}/{self.led_config["single"]}",
                                          self.gen_config["max_brightness"], self.gen_config["min_brightness"],
                                          single_mode=True, single=self.led_config[each])
            else:
                if each != "single":
                    self.led_objs[each] = LED(f"{self.gen_config['base']}/{self.led_config[each]}",
                                              self.gen_config["max_brightness"], self.gen_config["min_brightness"])
        self.max = config["general"]["max_brightness"]
        self.min = config["general"]["min_brightness"]
        self.absolute_max = config["general"]["max_brightness"]

    def get_all(self) -> dict:
        """Get the state of all LEDS in the array, represented by a dictionary"""
        output = {}
        for each in self.led_objs:
            output[each] = self.get_single(each)
        return output

    def get(self) -> int:
        """Compatability function to allow usage like LED(). Returns average of all brightnesses"""
        all_leds = self.get_all()
        avg = 0
        for each in all_leds:
            avg += all_leds[each]
        return round(avg / len(all_leds))

    def get_single(self, name: str) -> int:
        """Get the state of a single LED in the array"""
        return self.led_objs[name].get()

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

    def set_max_brightness(self):
        """Alias to set_all_max()"""
        self.set_all_max()

    def set_all_off(self):
        """Turn off all LEDs in the array"""
        self.set_all(0)

    def set_off(self):
        """Alias to set_all_off()"""
        self.set_all_off()

    def set_all(self, brightness: int):
        """Set brightness for all LEDs in array"""
        for each in self.led_objs:
            self.set_single(each, brightness)

    def set(self, brightness: int):
        """Compatability function to set all LED brightnesses in array"""
        self.set_all(brightness)

    def change_max_brightness(self, new_max: int):
        """Set max brightness for array so that brightness can be scaled"""
        for each in self.led_objs:
            self.led_objs[each].change_max_brightness(new_max)
        self.max = new_max

    def reset_max_brightness(self):
        """Set max brightness for array so that brightness can be scaled"""
        for each in self.led_objs:
            self.led_objs[each].reset_max_brightness()
        self.max = self.absolute_max

    def list_leds(self) -> tuple:
        """Return a tuple of all valid LEDs"""
        return tuple(self.led_objs.keys())

    def toggle(self):
        """Toggle all LEDs"""
        for each in self.led_objs:
            self.led_objs[each].toggle()


class Glyph(Array):
    """Object representation for Nothing Phone 1 Glyph Lights"""
    def __init__(self, config):
        super(Glyph, self).__init__(config)
        self.animation_key = {"name": None,
                              "cancel_time": None,
                              "animation_object": None}
        self.hardware_effects = [effect for effect in os.listdir(self.gen_config["base"]) if "effect" in effect]
        self.playing_hardware_animations = {}
        self.playing_software_animations = {}

    def play_hardware_animation(self, animation_name: str, duration=4000):
        """Play a hardware-enabled animation, duration in milliseconds"""
        if animation_name not in self.hardware_effects:
            raise NameError(f"Could not find effect `{animation_name}'. Try `Glyph().hardware_effects' to see available effects on your platform.")
        if duration in (-1, None):
            duration = 9999999999
        length = duration / 1000
        cancel_time = time.time() + length
        new_animation = self.animation_key
        new_animation["cancel_time"] = cancel_time
        new_animation["name"] = animation_name
        self.playing_hardware_animations[time.time()] = new_animation
        with open(f"{self.gen_config['base']}/{animation_name}", "w") as file:
            file.write("1")

    def stop_hardware_animation(self, animation_name: str):
        """Stop a playing hardware-enabled animation"""
        with open(f"{self.gen_config['base']}/{animation_name}", "w") as file:
            file.write("0")
        delete = []
        for each in self.playing_animations:
            if self.playing_animations[each]["name"] == animation_name:
                delete.append(each)
        for each in delete:
            del self.playing_hardware_animations[each]

    def check_status(self):
        """Check all running animations. If their cancel time is less than or equal to the current time, cancel the animation
        Check LED brightnesses and enforce that they are at or below their max brightness.
        """
        delete = set()
        for each in self.playing_hardware_animations:
            if self.playing_animations[each]["cancel_time"] <= time.time():
                delete.add(self.playing_animations[each]["name"])
        for each in delete:
            self.stop_hardware_animation(each)

        delete = set()
        for each in self.playing_software_animations:
            if self.playing_software_animations[each]["cancel_time"] <= time.time():
                delete.add(each)
            else:
                self.playing_software_animations[each]["animation_object"].tick()
        for each in delete:
            self.stop_software_animation(each)
        tools.enforce_brightness(self.led_objs)

    def play_software_animation(self, settings_obj, animation, leds="all", reason=None, duration=4000) -> str:
        """calls start() on the passed animation object. Assumes all LEDs by default. Returns a unique animation ID."""
        ani_obj = animation()
        ani_leds = {}
        if leds in ("all", ("all"), ["all"]):
            leds = self.gen_config["all"]
        if isinstance(leds, str):
            leds = [leds]
        for each in leds:
            ani_obj.add_led(each, self.led_objs[each])
        if reason is not None:
            # Later, we will add the ability to add a reason, so different things like notifications or alarms can play the same animation, but load different settings so they are distinct
            pass
        if duration in (-1, None):
            duration = 9999999999
        length = duration / 1000
        cancel_time = time.time() + length
        new_animation = self.animation_key
        new_animation["cancel_time"] = cancel_time
        new_animation["animation_object"] = ani_obj
        new_id = tools.gen_id()
        self.playing_software_animations[new_id] = new_animation
        self.playing_software_animations[new_id]["animation_object"].start()
        return new_id


    def stop_software_animation(self, animation_id: str):
        """Stops a given software animation, indicated by the animation ID, by calling the stop() method on it."""
        self.playing_software_animations[animation_id]["animation_object"].stop()
        del self.playing_software_animations[animation_id]

