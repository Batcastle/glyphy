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
import glob
import json
import os
import subprocess

UNIT = "glyphy.service"
UNIT_DIR = os.path.expanduser("~/.config/systemd/user")
APP_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
UNIT_SOURCE = os.path.join(APP_ROOT, "config", UNIT)
APP_DIR_PLACEHOLDER = "@APP_DIR@"
ACTIONS = ("start", "stop", "restart", "enable", "disable")
PROPERTIES = ("LoadState", "ActiveState", "UnitFileState")


def _systemctl(*args):
    # systemctl's output contains non-ASCII (e.g. the ● in `status`), so don't rely on the locale
    return subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=30)


def status() -> dict:
    """Return the unit's load state, active state, and enablement state"""
    result = _systemctl("show", UNIT, "--property=" + ",".join(PROPERTIES))
    output = dict.fromkeys(PROPERTIES, "")
    for line in result.stdout.splitlines():
        key, _, value = line.partition("=")
        if key in output:
            output[key] = value
    return output


def raw_status() -> str:
    """Return the output of `systemctl --user status glyphy.service`"""
    result = _systemctl("status", UNIT, "--no-pager", "--full")
    return (result.stdout + result.stderr).strip()


def version() -> str:
    """Return Glyphy's version.
    `click build` moves manifest.json out of the installed files, so after checking for it
    (present when running from a source tree), check the copy click keeps in .click/info,
    then fall back to the name of the version-numbered install directory."""
    candidates = [os.path.join(APP_ROOT, "manifest.json")]
    candidates += sorted(glob.glob(os.path.join(APP_ROOT, ".click", "info", "*.manifest")))
    for path in candidates:
        try:
            with open(path) as file:
                found = json.load(file).get("version")
        except (OSError, ValueError):
            continue
        if found:
            return str(found)
    if os.path.isdir(os.path.join(os.path.dirname(APP_ROOT), "current")):
        return os.path.basename(APP_ROOT)
    return ""


def run(action: str) -> dict:
    """Run a systemctl action on the Glyphy unit"""
    if action not in ACTIONS:
        return {"ok": False, "message": f"Unknown action: {action}"}
    result = _systemctl(action, UNIT)
    return {"ok": result.returncode == 0, "message": result.stderr.strip()}


def _app_dir() -> str:
    """Glyphy's install directory, via the click's "current" symlink when there is one,
    so the unit keeps pointing at the newest version after app updates"""
    current = os.path.join(os.path.dirname(APP_ROOT), "current")
    return current if os.path.isdir(current) else APP_ROOT


def install() -> dict:
    """Install config/glyphy.service as a user unit, filling in @APP_DIR@,
    then enable and start it"""
    try:
        with open(UNIT_SOURCE) as file:
            unit = file.read().replace(APP_DIR_PLACEHOLDER, _app_dir())
        os.makedirs(UNIT_DIR, exist_ok=True)
        with open(os.path.join(UNIT_DIR, UNIT), "w") as file:
            file.write(unit)
    except OSError as error:
        return {"ok": False, "message": f"Could not install {UNIT}: {error}"}
    for args in (("daemon-reload",), ("enable", "--now", UNIT)):
        result = _systemctl(*args)
        if result.returncode != 0:
            return {"ok": False, "message": result.stderr.strip()}
    return {"ok": True, "message": ""}


def uninstall() -> dict:
    """Stop and disable the unit, then remove its file"""
    _systemctl("disable", "--now", UNIT)
    try:
        os.remove(os.path.join(UNIT_DIR, UNIT))
    except FileNotFoundError:
        pass
    except OSError as error:
        return {"ok": False, "message": f"Could not remove {UNIT}: {error}"}
    _systemctl("daemon-reload")
    _systemctl("reset-failed", UNIT)
    return {"ok": True, "message": ""}


def reinstall() -> dict:
    """Remove the unit, then install a fresh copy from config/glyphy.service"""
    result = uninstall()
    if not result["ok"]:
        return result
    return install()
