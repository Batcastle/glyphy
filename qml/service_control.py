#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  service_control.py
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
"""systemctl wrapper used by the Glyphy settings app"""
import os
import subprocess

UNIT = "glyphy.service"
UNIT_DIR = os.path.expanduser("~/.config/systemd/user")
APP_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
UNIT_TEMPLATE = """[Unit]
Description=Glyphy glyph light daemon
Conflicts=glyphs.service

[Service]
ExecStart=/usr/bin/python3 -u {daemon}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"""
ACTIONS = ("start", "stop", "restart", "enable", "disable")
PROPERTIES = ("LoadState", "ActiveState", "UnitFileState")


def _systemctl(*args):
    return subprocess.run(["systemctl", "--user", *args],
                          capture_output=True, text=True, timeout=30)


def status() -> dict:
    """Return the unit's load state, active state, and enablement state"""
    result = _systemctl("show", UNIT, "--property=" + ",".join(PROPERTIES))
    output = dict.fromkeys(PROPERTIES, "")
    for line in result.stdout.splitlines():
        key, _, value = line.partition("=")
        if key in output:
            output[key] = value
    return output


def run(action: str) -> dict:
    """Run a systemctl action on the Glyphy unit"""
    if action not in ACTIONS:
        return {"ok": False, "message": f"Unknown action: {action}"}
    result = _systemctl(action, UNIT)
    return {"ok": result.returncode == 0, "message": result.stderr.strip()}


def _daemon_path() -> str:
    """Path to glyphyd.py, via the click's "current" symlink when there is one,
    so the unit keeps working after app updates"""
    current = os.path.join(os.path.dirname(APP_ROOT), "current")
    root = current if os.path.isdir(current) else APP_ROOT
    return os.path.join(root, "src", "glyphyd.py")


def install() -> dict:
    """Write the user unit, then enable it and start it"""
    try:
        os.makedirs(UNIT_DIR, exist_ok=True)
        with open(os.path.join(UNIT_DIR, UNIT), "w") as file:
            file.write(UNIT_TEMPLATE.format(daemon=_daemon_path()))
    except OSError as error:
        return {"ok": False, "message": f"Could not write {UNIT}: {error}"}
    for args in (("daemon-reload",), ("enable", "--now", UNIT)):
        result = _systemctl(*args)
        if result.returncode != 0:
            return {"ok": False, "message": result.stderr.strip()}
    return {"ok": True, "message": ""}
