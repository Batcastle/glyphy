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
import signal
import sys
import subprocess
import os
import settings
import led
import tools


CONFIG = settings.Settings()
CONFIG.search()
CONFIG.load()
GENERAL_SETTINGS = CONFIG.get("general.json")
glyphs = led.Glyph(GENERAL_SETTINGS)
# This was here for stopping the glyph-lights service, which we are working on replacing.
# subprocess.check_call(["systemctl", "--user", "stop", "glyphs"])


def _shutdown(_signum, _frame):
       glyphs.set_all_off()
       sys.exit(0)


signal.signal(signal.SIGTERM, _shutdown)
screen = tools.ScreenBrightnessFollower()
notifications = tools.NotificationWatcher()
file_watcher = tools.FileWatcher()
loop_delay = 1 / GENERAL_SETTINGS["general"]["loop_frequency"]
file_watcher_delay = 1 / GENERAL_SETTINGS["general"]["file_check_frequency"]
last_file_check = time.time()
# length = 90
# finish = time.time() + length
ids = {
        "unread_id": None,
        "wireless_charging_id": None,
        "charging_id": None,
        "recording_id": None
    }
# while time.time() <= finish:
while True:
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


    if tools.is_recording_video():
        if ids["recording_id"] is None:
            ids["recording_id"] = glyphs.play_animation(CONFIG, reason="recording")
    elif ids["recording_id"] is not None:
        glyphs.stop_software_animation(ids["recording_id"])
        ids["recording_id"] = None


    if time.time() >= (last_file_check + file_watcher_delay):
        last_file_check = time.time()
        if file_watcher.update_contents() or file_watcher.hash_contents():
            break
    glyphs.check_status()
    time.sleep(loop_delay)


glyphs.set_all_off()
# If we get down here, Glyphy has either been updated or removed. Determine which...
if not os.path.isdir(file_watcher.directory):
    # We've been removed. Remove the unit file, turn off the lights, and go quietly into that good night
    subprocess.check_call(["systemctl", "--user", "disable", "glyphy.service"])
    try:
        os.remove(os.path.expanduser("~/.config/systemd/user/glyphy.service"))
    except FileNotFoundError:
        pass
    subprocess.run(["systemctl", "--user", "daemon-reload"])
else:
    # If we didn't go into that if statement above, then we just got updated. Don't remove the unit file, but do turn off the lights as we do not go quietly into that good night
    # We do have to exit on failure though so that systemd restarts us.
    sys.exit(75)

