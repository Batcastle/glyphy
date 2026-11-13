#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  settings.py
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
"""Load Glyphy settings"""
import json
import os

# Defaults ship read-only in the click package; the user's changes live here, as partial
# copies of the default files that only contain the keys they changed
USER_PATH = os.path.join(os.path.expanduser("~"), ".config", "glyphy.batcastle")


def merge(base: dict, overrides: dict) -> dict:
    """Recursively merge overrides into a copy of base"""
    output = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(output.get(key), dict):
            output[key] = merge(output[key], value)
        else:
            output[key] = value
    return output


class Settings:
    """Settings access class"""
    def __init__(self):
        """Setup settings class"""
        self.files = {}
        self.settings = {}
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")
        self.user_path = USER_PATH

    def search(self, path=None) -> dict:
        """Check filesystem for available config files"""
        if path is None:
            path = self.path
        files = os.listdir(path)
        output = {}
        for each in files:
            if each[-5:] != ".json":
                continue
            output[each] = {"name": f"{path}/{each}",
                           "type": None,
                           "children": {},
                           "size": os.stat(f"{path}/{each}")[6]}
            if os.path.isfile(f"{path}/{each}"):
                output[each]["type"] = "file"
            elif os.path.isdir(f"{path}/{each}"):
                output[each]["type"] = "dir"
                output[each]["children"] = self.search(path=f"{path}/{each}")
        if path == self.path:
            self.files = output
        return output

    def load(self, files_to_process=None):
        """Load settings to memory"""
        if files_to_process is None:
            files_to_process = self.files
        output = {}
        for each in files_to_process:
            if files_to_process[each]["type"] == "file":
                with open(files_to_process[each]["name"], "r") as file:
                    key = os.path.relpath(files_to_process[each]["name"], self.path)
                    try:
                        output[key] = json.load(file)
                    except json.decoder.JSONDecodeError:
                        print(f"JSON formatting error in file: {files_to_process[each]["name"]} ; not importing...")
            elif files_to_process[each]["type"] == "dir":
                output = output | self.load(files_to_process=files_to_process[each]["children"])
        if files_to_process == self.files:
            output = self._apply_overrides(output)
            self.settings = output
        return output

    def _apply_overrides(self, defaults: dict) -> dict:
        """Merge the user's override files over the defaults"""
        output = {}
        for key, value in defaults.items():
            user_file = os.path.join(self.user_path, key)
            try:
                with open(user_file, "r") as file:
                    output[key] = merge(value, json.load(file))
            except FileNotFoundError:
                output[key] = value
            except json.decoder.JSONDecodeError:
                print(f"JSON formatting error in file: {user_file} ; ignoring user settings...")
                output[key] = value
        return output

    def save_overrides(self, changes: dict):
        """Merge partial settings into the user's override files.
        `changes` maps a settings file name to a partial copy of that file,
        e.g. {"animations.json": {"animations": {"recording": {"enabled": False}}}}"""
        for key, partial in changes.items():
            user_file = os.path.join(self.user_path, key)
            try:
                with open(user_file, "r") as file:
                    current = json.load(file)
            except (FileNotFoundError, json.decoder.JSONDecodeError):
                current = {}
            os.makedirs(os.path.dirname(user_file), exist_ok=True)
            temp_file = f"{user_file}.tmp"
            with open(temp_file, "w") as file:
                json.dump(merge(current, partial), file, indent=2)
            os.replace(temp_file, user_file)

    def get(self, filename):
        """Get contents of settings file"""
        return self.settings[filename]
