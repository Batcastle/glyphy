#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  glyphyd.py
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
"""Daemon to control Glyph lights"""
import time
import json
import multiprocessing
import subprocess
import settings
from led import LED

print("THIS IS A TEST!")
print("LOADING SETTINGS...")
CONFIG = settings.Settings()
CONFIG.search()
CONFIG.load()
GENERAL_SETTINGS = CONFIG.get("../config/general.json")
print("SETTINGS LOADED")

print("SETTING UP LED OBJECTS...")
LED_OBJS = {}
for EACH in GENERAL_SETTINGS["leds"]:
    if not isinstance(GENERAL_SETTINGS["leds"][EACH], list):
        LED_OBJS[EACH] = LED(f"{GENERAL_SETTINGS['general']['base']}/{GENERAL_SETTINGS['leds'][EACH]}", GENERAL_SETTINGS["general"]["max_brightness"], GENERAL_SETTINGS["general"]["min_brightness"])
print("LED OBJECTS SETUP")

print("DISABLING GLYPH LIGHTS SERVICE")
subprocess.check_call(["systemctl", "--user", "stop", "glyphs"])

print("TESTING...")
OUTPUT = {}
for EACH in LED_OBJS:
    LED_OBJS[EACH].set(LED_OBJS[EACH].max)
    result = input(f"Is the LED {EACH} turned on?: ").lower()
    if result in ("y", "yes"):
        OUTPUT[EACH] = True
    else:
        OUTPUT[EACH] = False
    LED_OBJS[EACH].set(LED_OBJS[EACH].min)
print("TESTING COMPLETE!")
print("RE-STARTING GLYPH LIGHTS SERVICE")
subprocess.check_call(["systemctl", "--user", "start", "glyphs"])
print("CURRENT LED STATUS:")
print(json.dumps(OUTPUT, indent=2))



