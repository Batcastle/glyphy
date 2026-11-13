#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  settings_control.py
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
"""Read and save Glyphy settings for the settings app, using the daemon's own modules,
so hooks, animations, and LEDs are discovered the same way the daemon sees them"""
import inspect
import os
import sys

APP_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(APP_ROOT, "src"))

import settings  # noqa: E402  (needs the sys.path entry above)
import animations  # noqa: E402


def _tidy(name: str) -> str:
    words = name.replace("_", " ").strip()
    return words[:1].upper() + words[1:]


def _load() -> settings.Settings:
    config = settings.Settings()
    config.search()
    config.load()
    return config


def _software_patterns() -> list:
    """Software animations from animations.init(), with the parameters each one accepts.
    A class can describe its parameters with a PARAMETERS dict, e.g.
    {"frequency": {"unit": "Hz", "min": 0.1, "max": 10}}; otherwise a `frequency` argument
    with a real default on start() is offered."""
    output = []
    for cls in animations.init().values():
        parameters = {}
        try:
            signature = inspect.signature(cls.start).parameters
        except (TypeError, ValueError):
            signature = {}
        declared = getattr(cls, "PARAMETERS", None)
        if isinstance(declared, dict):
            for name, info in declared.items():
                entry = dict(info) if isinstance(info, dict) else {}
                if "default" not in entry and name in signature \
                        and signature[name].default is not inspect.Parameter.empty:
                    entry["default"] = signature[name].default
                parameters[name] = entry
        elif "frequency" in signature and signature["frequency"].default not in (None, inspect.Parameter.empty):
            parameters["frequency"] = {"unit": "Hz", "default": signature["frequency"].default}
        output.append({"value": cls.__name__, "label": cls.__name__,
                       "hardware": False, "parameters": parameters})
    return output


def _hardware_patterns(base: str) -> list:
    """Hardware effects, discovered the same way led.Glyph does"""
    try:
        names = sorted(name for name in os.listdir(base) if "effect" in name)
    except OSError:
        names = []
    return [{"value": name, "label": _tidy(name), "hardware": True, "parameters": {}}
            for name in names]


def hooks() -> dict:
    """Everything the settings tab needs: each hook in animations.json with its current
    settings (defaults plus the user's changes), the animations it can use, and the LEDs"""
    try:
        config = _load()
        hook_settings = config.get("animations.json")["animations"]
        general = config.get("general.json")
        patterns = _software_patterns() + _hardware_patterns(general["general"]["base"])
        # "single" is the shared brightness file for single-mode LEDs, not an LED itself
        leds = [name for name in general["leds"] if name != "single"]

        items = []
        known = {pattern["value"].lower() for pattern in patterns}
        for key, value in hook_settings.items():
            pattern = str(value.get("pattern", ""))
            hardware = bool(value.get("hardware", pattern.lower().endswith("_effect")))
            if pattern and pattern.lower() not in known:
                # Keep a configured animation selectable even if it isn't available right now
                patterns.append({"value": pattern, "label": f"{pattern} (unavailable)",
                                 "hardware": hardware, "parameters": {}})
                known.add(pattern.lower())
            hook_leds = value.get("leds", ["all"])
            if isinstance(hook_leds, str):
                hook_leds = [hook_leds]
            items.append({
                "key": key,
                "name": value.get("name") or _tidy(key),
                "description": value.get("description", ""),
                "enabled": bool(value.get("enabled", True)),
                "pattern": pattern,
                "leds": list(hook_leds),
                "frequency": value.get("frequency"),
                "duration": value.get("duration", -1),
            })
    except Exception as error:  # report anything to the UI instead of leaving it waiting
        return {"ok": False, "message": f"Could not load settings: {error}",
                "hooks": [], "patterns": [], "leds": []}
    return {"ok": True, "message": "", "hooks": items, "patterns": patterns, "leds": leds}


def general() -> dict:
    """Everything in general.json except the "leds" mapping, as a flat list of fields.
    Each field has a path (e.g. ["general", "loop_frequency"]), a kind that tells the UI
    which control to show, and its current value (defaults plus the user's changes)."""
    try:
        config = _load()
        data = config.get("general.json")
        leds = [name for name in data.get("leds", {}) if name != "single"]
        fields = []

        def add(path, value):
            if isinstance(value, bool):
                kind = "bool"
            elif isinstance(value, int):
                kind = "int"
            elif isinstance(value, float):
                kind = "float"
            elif isinstance(value, str):
                kind = "string"
            elif isinstance(value, list) and value and all(item in leds for item in value):
                kind = "leds"
            elif isinstance(value, list):
                kind = "list"
            else:
                return  # nested objects aren't editable here
            fields.append({"path": path, "kind": kind, "value": value})

        for section, content in data.items():
            if section == "leds":
                continue
            if isinstance(content, dict):
                for key, value in content.items():
                    add([section, key], value)
            else:
                add([section], content)
    except Exception as error:  # report anything to the UI instead of leaving it waiting
        return {"ok": False, "message": f"Could not load settings: {error}", "fields": [], "leds": []}
    return {"ok": True, "message": "", "fields": fields, "leds": leds}


def reset(filename: str) -> dict:
    """Restore the defaults for one settings file by removing the user's changes to it"""
    try:
        _load().clear_overrides(filename)
    except Exception as error:  # report anything to the UI instead of leaving it waiting
        return {"ok": False, "message": f"Could not restore defaults: {error}"}
    return {"ok": True, "message": ""}


def _match_types(changes, reference):
    """QML hands every number to Python as a float, so 10 arrives as 10.0. Turn whole-number
    floats back into ints wherever the existing setting is an int (e.g. brightness values,
    which are written straight to sysfs)."""
    if isinstance(changes, dict) and isinstance(reference, dict):
        return {key: _match_types(value, reference.get(key)) for key, value in changes.items()}
    if isinstance(changes, float) and changes.is_integer() \
            and isinstance(reference, int) and not isinstance(reference, bool):
        return int(changes)
    return changes


def save(changes: dict) -> dict:
    """Save partial settings, e.g. {"animations.json": {"animations": {"recording": {"enabled": False}}}}"""
    try:
        config = _load()
        changes = {key: _match_types(value, config.settings.get(key)) for key, value in changes.items()}
        config.save_overrides(changes)
    except Exception as error:  # report anything to the UI instead of leaving it waiting
        return {"ok": False, "message": f"Could not save settings: {error}"}
    return {"ok": True, "message": ""}
