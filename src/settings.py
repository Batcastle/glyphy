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

    def search(self, path="../config") -> dict:
        """Check filesystem for available config files"""
        files = os.listdir(path)
        output = {}
        for each in files:
            output[each] = {"name": each,
                           "type": None,
                           "children": {},
                           "size": os.stat(f"{path}/{each}")[6]}
            if os.path.isfile(f"{path}/{each}"):
                output[each]["type"] = "file"
            elif os.path.isdir(f"{path}/{each}"):
                output[each]["type"] = "dir"
                output[each]["children"] = self.search(path=f"{path}/{each}")
        if path == "../config":
            self.files = output
        return output

    def load(self):
        """Load settings to memory"""

    def get(self, filename):
        """Get contents of settings file"""
