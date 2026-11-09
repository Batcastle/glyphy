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
import tools


CONFIG = settings.Settings()
CONFIG.search()
CONFIG.load()
GENERAL_SETTINGS = CONFIG.get("../config/general.json")
ANIMATION_SETTINGS = CONFIG.get("../config/animations.json")
glyphs = led.Array(GENERAL_SETTINGS)
glyph_system = led.Glyph(GENERAL_SETTINGS)
subprocess.check_call(["systemctl", "--user", "stop", "glyphs"])
screen = tools.ScreenBrightnessFollower()
length = 30
finish = time.time() + length
while time.time() <= finish:
    brightness = screen.get()
    brightness = brightness * glyphs.led_objs["G"].max
    glyphs.set("G", brightness)


subprocess.check_call(["systemctl", "--user", "start", "glyphs"])
print("CURRENT LED STATUS:")
print(json.dumps(OUTPUT, indent=2))


