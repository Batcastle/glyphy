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


class Settings:
    """Settings access class"""
    def __init__(self):
        """Setup settings class"""
        self.files = {}
        self.settings = {}
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")

    def search(self, path=None) -> dict:
        """Check filesystem for available config files"""
        if path is None:
            path = self.path
        files = os.listdir(path)
        output = {}
        for each in files:
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
                    try:
                        output[files_to_process[each]["name"]] = json.load(file)
                    except json.decoder.JSONDecodeError:
                        print(f"JSON formatting error in file: {files_to_process[each]["name"]} ; not importing...")
            elif files_to_process[each]["type"] == "dir":
                output = output | self.load(files_to_process=files_to_process[each]["children"])
        if files_to_process == self.files:
            self.settings = output
        return output

    def get(self, filename):
        """Get contents of settings file"""
        return self.settings[filename]
