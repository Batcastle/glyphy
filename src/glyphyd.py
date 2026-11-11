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
# import multiprocessing
import subprocess
import settings
import led
import tools


CONFIG = settings.Settings()
CONFIG.search()
CONFIG.load()
GENERAL_SETTINGS = CONFIG.get("../config/general.json")
glyphs = led.Glyph(GENERAL_SETTINGS)
subprocess.check_call(["systemctl", "--user", "stop", "glyphs"])
screen = tools.ScreenBrightnessFollower()
notifications = tools.NotificationWatcher()
length = 90
finish = time.time() + length
ids = {
        "unread_id": None,
        "wireless_charging_id": None,
        "charging_id": None
    }
while time.time() <= finish:
    glyphs.check_status()

    if notifications.new_notification():
        glyphs.play_animation(CONFIG, reason="notification")
    if tools.has_notifications():
        if ids["unread_id"] is None:
            ids["unread_id"] = glyphs.play_animation(CONFIG, reason="unread")
    elif ids["unread_id"] is not None:
        glyphs.stop_software_animation(ids["unread_id"])
        ids["unread_id"] = None

    if tools.is_wireless_charging():
        if ids["wireless_charging_id"] is None:
            ids["wireless_charging_id"] = glyphs.play_animation(CONFIG, reason="wireless_charging")
    elif ids["wireless_charging_id"] is not None:
        glyphs.stop_software_animation(ids["wireless_charging_id"])
        ids["wireless_charging_id"] = None

    if tools.is_wireless_charging() or tools.is_charging(wired_only=True):
        if ids["charging_id"] is None:
            ids["charging_id"] = glyphs.play_animation(CONFIG, reason="charging")
    elif ids["charging_id"] is not None:
        glyphs.stop_software_animation(ids["charging_id"])
        ids["charging_id"] = None


    glyphs.check_status()



glyphs.set_all_off()
subprocess.check_call(["systemctl", "--user", "start", "glyphs"])
