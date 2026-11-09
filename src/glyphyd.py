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
import led

print("THIS IS A TEST!")
print("LOADING SETTINGS...")
CONFIG = settings.Settings()
CONFIG.search()
CONFIG.load()
GENERAL_SETTINGS = CONFIG.get("../config/general.json")
print("SETTINGS LOADED")

print("SETTING UP LED OBJECTS...")
glyphs = led.Array(GENERAL_SETTINGS)
print("LED OBJECTS SETUP")

print("DISABLING GLYPH LIGHTS SERVICE")
subprocess.check_call(["systemctl", "--user", "stop", "glyphs"])

print("TESTING...")
OUTPUT = {}
for EACH in glyphs.list_leds():
    print(f"TESTING {EACH}...")
    glyphs.set_single_max(EACH)
    result = input(f"Is the LED {EACH} turned on?: ").lower()
    if result in ("y", "yes"):
        OUTPUT[EACH] = True
    else:
        OUTPUT[EACH] = False
    glyphs.set_single_off(EACH)
print("TESTING BAR SEGMENTATION...")
print("Please watch bar for progress bar animation...")
for each in glyphs.led_objs["bar"]:
    glyphs.led_objs["bar"][each].set(glyphs.led_objs["bar"][each].max)
    time.sleep(1)
glyphs.led_objs["bar"].set_all_off()
result = input("Did the progress bar animation play correctly?: ").lower()
if result in ("y", "yes"):
    OUTPUT["progress"] = True
else:
    OUTPUT["progress"] = False
print("TESTING COMPLETE!")
print("RE-STARTING GLYPH LIGHTS SERVICE")
subprocess.check_call(["systemctl", "--user", "start", "glyphs"])
print("CURRENT LED STATUS:")
print(json.dumps(OUTPUT, indent=2))

print("TESTING NEW GLYPH CLASS")
glyphs = led.Glyph(GENERAL_SETTINGS)
print(f"Known effects: {glyphs.effects}")



