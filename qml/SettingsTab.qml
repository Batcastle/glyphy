/*
 * Copyright (C) 2026  Thomas Castleman
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; version 3.
 *
 * glyphy is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
import QtQuick 2.7
import QtQuick.Layouts 1.3
import Lomiri.Components 1.3

// User settings, built entirely from what settings_control.hooks() reports: every hook in
// animations.json, the animations available to it, and the LEDs. Changes are staged here
// and only written when Save is pressed, then the service is restarted to pick them up.
Item {
    id: settingsTab
    property var app

    readonly property bool ready: app ? app.settingsReady : false
    property bool loaded: false
    property bool saving: false
    property int pendingChanges: 0
    property bool allValid: true
    property string message: ""
    property bool messageIsError: false

    // [{value, label, hardware, parameters: {name: {unit, min, max, default}}}]
    property var patterns: []
    property var patternLabels: []
    // LED names from general.json, in config order
    property var ledNames: []

    // ---- Helpers ----

    function tidy(name) {
        var words = name.replace(/_/g, " ")
        return words.charAt(0).toUpperCase() + words.slice(1)
    }

    function patternIndex(value) {
        var wanted = String(value).toLowerCase()
        for (var i = 0; i < patterns.length; i++)
            if (patterns[i].value.toLowerCase() === wanted)
                return i
        return -1
    }

    function patternFor(value) {
        var i = patternIndex(value)
        return i >= 0 ? patterns[i] : {"value": value, "label": value, "hardware": false, "parameters": {}}
    }

    function hasParameter(value, name) {
        return patternFor(value).parameters[name] !== undefined
    }

    function parameterInfo(value, name) {
        return patternFor(value).parameters[name] || {}
    }

    // LED selections are kept as comma-separated strings, because ListModel turns
    // JS arrays into nested models
    function ledList(leds) {
        return leds === "" ? [] : leds.split(",")
    }

    function setLed(row, name, checked) {
        var current = ledList(hookModel.get(row).leds)
        var updated = []
        if (name === "all") {
            updated = checked ? ["all"] : []
        } else {
            for (var i = 0; i < ledNames.length; i++) {
                var led = ledNames[i]
                var on = led === name ? checked : current.indexOf(led) >= 0
                if (on)
                    updated.push(led)
            }
        }
        hookModel.setProperty(row, "leds", updated.join(","))
        countChanges()
    }

    function isNumber(text, integer) {
        return (integer ? /^[0-9]+$/ : /^[0-9]*\.?[0-9]+$/).test(text) && parseFloat(text) > 0
    }

    function rowChanges(row) {
        var changes = {}
        if (row.enabled !== row.savedEnabled)
            changes.enabled = row.enabled
        if (row.pattern !== row.savedPattern) {
            changes.pattern = row.pattern
            changes.hardware = patternFor(row.pattern).hardware
        }
        var hardware = patternFor(row.pattern).hardware
        if (!hardware && row.leds !== row.savedLeds)
            changes.leds = ledList(row.leds)
        if (hasParameter(row.pattern, "frequency") && row.frequency !== row.savedFrequency
                && isNumber(row.frequency, false))
            changes.frequency = parseFloat(row.frequency)
        if (row.showDuration && row.duration !== row.savedDuration && isNumber(row.duration, true))
            changes.duration = parseInt(row.duration)
        return changes
    }

    function rowValid(row) {
        if (!patternFor(row.pattern).hardware && ledList(row.leds).length === 0)
            return false
        if (hasParameter(row.pattern, "frequency") && !isNumber(row.frequency, false))
            return false
        if (row.showDuration && !isNumber(row.duration, true))
            return false
        return true
    }

    function countChanges() {
        var count = 0
        var valid = true
        for (var i = 0; i < hookModel.count; i++) {
            var row = hookModel.get(i)
            // "hardware" follows the chosen animation, so it isn't a separate change
            count += Object.keys(rowChanges(row)).filter(function(name) { return name !== "hardware" }).length
            if (!rowValid(row))
                valid = false
        }
        pendingChanges = count
        allValid = valid
    }

    // ---- Loading and saving ----

    function load() {
        app.callPython("settings_control.hooks", [], function(result) {
            patterns = result.patterns
            var labels = []
            for (var p = 0; p < result.patterns.length; p++)
                labels.push(result.patterns[p].label)
            patternLabels = labels
            ledNames = result.leds

            hookModel.clear()
            for (var i = 0; i < result.hooks.length; i++) {
                var hook = result.hooks[i]
                var frequency = hook.frequency !== null && hook.frequency !== undefined
                        ? String(hook.frequency)
                        : String(parameterInfo(hook.pattern, "frequency").default || "")
                var leds = hook.leds.join(",")
                var duration = String(hook.duration)
                hookModel.append({
                    "key": hook.key, "name": hook.name, "description": hook.description,
                    "enabled": hook.enabled, "savedEnabled": hook.enabled,
                    "pattern": hook.pattern, "savedPattern": hook.pattern,
                    "leds": leds, "savedLeds": leds,
                    "frequency": frequency, "savedFrequency": frequency,
                    "duration": duration, "savedDuration": duration,
                    // Hooks that run until their condition clears use -1 and get no length setting
                    "showDuration": hook.duration !== -1
                })
            }
            loaded = result.ok
            if (!result.ok) {
                message = result.message
                messageIsError = true
            }
            countChanges()
        })
    }

    function discard() {
        for (var i = 0; i < hookModel.count; i++) {
            var row = hookModel.get(i)
            hookModel.set(i, {"enabled": row.savedEnabled, "pattern": row.savedPattern,
                              "leds": row.savedLeds, "frequency": row.savedFrequency,
                              "duration": row.savedDuration})
        }
        message = ""
        countChanges()
    }

    function save() {
        var animations = {}
        for (var i = 0; i < hookModel.count; i++) {
            var changes = rowChanges(hookModel.get(i))
            if (Object.keys(changes).length > 0)
                animations[hookModel.get(i).key] = changes
        }
        saving = true
        message = ""
        app.callPython("settings_control.save", [{"animations.json": {"animations": animations}}],
                       function(result) {
            if (!result.ok) {
                saving = false
                message = result.message
                messageIsError = true
                return
            }
            for (var j = 0; j < hookModel.count; j++) {
                var row = hookModel.get(j)
                hookModel.set(j, {"savedEnabled": row.enabled, "savedPattern": row.pattern,
                                  "savedLeds": row.leds, "savedFrequency": row.frequency,
                                  "savedDuration": row.duration})
            }
            countChanges()

            if (!(app.installed && app.running)) {
                saving = false
                messageIsError = false
                message = app.installed
                        ? i18n.tr("Saved. Glyphy isn't running, so the changes will apply when it starts.")
                        : i18n.tr("Saved. The changes will apply once the Glyphy service is installed and running.")
                return
            }
            app.callPython("service_control.run", ["restart"], function(restart) {
                saving = false
                messageIsError = !restart.ok
                message = restart.ok
                        ? i18n.tr("Saved, and Glyphy restarted to apply the changes.")
                        : i18n.tr("Saved, but restarting Glyphy failed: %1").arg(restart.message)
                app.refresh()
                app.refreshRawStatus()
            })
        })
    }

    onReadyChanged: if (ready) load()

    ListModel {
        id: hookModel
    }

    // ---- Layout ----

    Flickable {
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            bottom: saveBar.top
        }
        contentHeight: column.height
        clip: true

        Column {
            id: column
            width: parent.width

            Item {
                width: parent.width
                height: sectionLabel.height + units.gu(3)

                Label {
                    id: sectionLabel
                    anchors {
                        left: parent.left
                        right: parent.right
                        bottom: parent.bottom
                        leftMargin: units.gu(2)
                        rightMargin: units.gu(2)
                        bottomMargin: units.gu(1)
                    }
                    text: i18n.tr("Animations")
                    textSize: Label.Large
                    font.weight: Font.DemiBold
                }
            }

            Repeater {
                model: hookModel

                delegate: Column {
                    id: hookItem
                    width: column.width

                    property bool expanded: false
                    readonly property int row: index
                    readonly property string patternValue: model.pattern
                    readonly property string ledsValue: model.leds
                    readonly property bool hardware: settingsTab.patternFor(patternValue).hardware
                    readonly property bool hasFrequency: settingsTab.hasParameter(patternValue, "frequency")

                    ListItem {
                        height: hookLayout.height + (divider.visible ? divider.height : 0)
                        divider.visible: !hookItem.expanded
                        onClicked: hookItem.expanded = !hookItem.expanded

                        ListItemLayout {
                            id: hookLayout
                            title.text: model.name
                            subtitle.text: model.description
                            subtitle.maximumLineCount: hookItem.expanded ? 20 : 2
                            subtitle.wrapMode: Text.WordWrap

                            Icon {
                                SlotsLayout.position: SlotsLayout.Trailing
                                width: units.gu(2)
                                height: width
                                name: hookItem.expanded ? "go-up" : "go-down"
                            }

                            Switch {
                                SlotsLayout.position: SlotsLayout.Trailing
                                checked: model.enabled
                                enabled: !settingsTab.saving
                                onCheckedChanged: {
                                    if (checked !== model.enabled) {
                                        hookModel.setProperty(hookItem.row, "enabled", checked)
                                        settingsTab.countChanges()
                                    }
                                }
                            }
                        }
                    }

                    // Per-hook settings, shown when the row is expanded
                    Column {
                        visible: hookItem.expanded
                        x: units.gu(2)
                        width: parent.width - units.gu(4)
                        spacing: units.gu(1.5)
                        enabled: !settingsTab.saving

                        OptionSelector {
                            width: parent.width
                            text: i18n.tr("Animation")
                            model: settingsTab.patternLabels
                            selectedIndex: Math.max(0, settingsTab.patternIndex(hookItem.patternValue))
                            onDelegateClicked: {
                                hookModel.setProperty(hookItem.row, "pattern", settingsTab.patterns[index].value)
                                settingsTab.countChanges()
                            }
                        }

                        Label {
                            visible: hookItem.hardware
                            width: parent.width
                            wrapMode: Text.Wrap
                            textSize: Label.Small
                            text: i18n.tr("This is a hardware effect, so it chooses its own lights and speed.")
                        }

                        Label {
                            visible: !hookItem.hardware
                            text: i18n.tr("Lights")
                        }

                        Flow {
                            visible: !hookItem.hardware
                            width: parent.width
                            spacing: units.gu(2)

                            Repeater {
                                model: ["all"].concat(settingsTab.ledNames)

                                delegate: Row {
                                    spacing: units.gu(1)
                                    readonly property bool allSelected: hookItem.ledsValue === "all"

                                    CheckBox {
                                        anchors.verticalCenter: parent.verticalCenter
                                        checked: modelData === "all"
                                                 ? parent.allSelected
                                                 : !parent.allSelected && settingsTab.ledList(hookItem.ledsValue).indexOf(modelData) >= 0
                                        enabled: modelData === "all" || !parent.allSelected
                                        onClicked: settingsTab.setLed(hookItem.row, modelData, checked)
                                    }
                                    Label {
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: modelData === "all" ? i18n.tr("All") : settingsTab.tidy(modelData)
                                    }
                                }
                            }
                        }

                        Label {
                            visible: !hookItem.hardware && settingsTab.ledList(hookItem.ledsValue).length === 0
                            color: theme.palette.normal.negative
                            textSize: Label.Small
                            text: i18n.tr("Choose at least one light.")
                        }

                        RowLayout {
                            visible: hookItem.hasFrequency
                            width: parent.width
                            spacing: units.gu(1)

                            Label {
                                Layout.fillWidth: true
                                wrapMode: Text.Wrap
                                text: {
                                    var unit = settingsTab.parameterInfo(hookItem.patternValue, "frequency").unit || "Hz"
                                    return i18n.tr("Speed (%1)").arg(unit)
                                }
                            }
                            TextField {
                                Layout.preferredWidth: units.gu(12)
                                text: model.frequency
                                inputMethodHints: Qt.ImhFormattedNumbersOnly
                                hasClearButton: false
                                errorHighlight: true
                                validator: RegExpValidator { regExp: /^[0-9]*\.?[0-9]*$/ }
                                onTextChanged: {
                                    if (text !== model.frequency) {
                                        hookModel.setProperty(hookItem.row, "frequency", text)
                                        settingsTab.countChanges()
                                    }
                                }
                            }
                        }

                        RowLayout {
                            visible: model.showDuration
                            width: parent.width
                            spacing: units.gu(1)

                            Label {
                                Layout.fillWidth: true
                                wrapMode: Text.Wrap
                                text: i18n.tr("Length (ms)")
                            }
                            TextField {
                                Layout.preferredWidth: units.gu(12)
                                text: model.duration
                                inputMethodHints: Qt.ImhDigitsOnly
                                hasClearButton: false
                                errorHighlight: true
                                validator: RegExpValidator { regExp: /^[0-9]*$/ }
                                onTextChanged: {
                                    if (text !== model.duration) {
                                        hookModel.setProperty(hookItem.row, "duration", text)
                                        settingsTab.countChanges()
                                    }
                                }
                            }
                        }

                        Item {
                            width: parent.width
                            height: units.gu(0.5)
                        }
                    }

                    Rectangle {
                        visible: hookItem.expanded
                        width: parent.width
                        height: units.dp(1)
                        color: theme.palette.normal.base
                    }
                }
            }

            Label {
                x: units.gu(2)
                width: parent.width - units.gu(4)
                visible: settingsTab.loaded && hookModel.count === 0
                wrapMode: Text.Wrap
                text: i18n.tr("No animations are configured.")
            }
        }
    }

    Item {
        id: saveBar
        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }
        height: saveColumn.height + units.gu(4)

        Rectangle {
            anchors {
                top: parent.top
                left: parent.left
                right: parent.right
            }
            height: units.dp(1)
            color: theme.palette.normal.base
        }

        ColumnLayout {
            id: saveColumn
            anchors {
                top: parent.top
                left: parent.left
                right: parent.right
                topMargin: units.gu(2)
                leftMargin: units.gu(2)
                rightMargin: units.gu(2)
            }
            spacing: units.gu(1)

            Label {
                Layout.fillWidth: true
                visible: settingsTab.message !== "" || !settingsTab.allValid
                wrapMode: Text.Wrap
                color: (settingsTab.messageIsError || !settingsTab.allValid)
                       ? theme.palette.normal.negative
                       : theme.palette.normal.backgroundSecondaryText
                text: !settingsTab.allValid ? i18n.tr("Some settings need fixing before you can save.")
                                            : settingsTab.message
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: units.gu(1)

                ActivityIndicator {
                    running: settingsTab.saving
                    visible: settingsTab.saving
                }

                Button {
                    visible: settingsTab.pendingChanges > 0 || !settingsTab.allValid
                    text: i18n.tr("Discard")
                    enabled: !settingsTab.saving
                    onClicked: settingsTab.discard()
                }

                Button {
                    Layout.fillWidth: true
                    text: settingsTab.pendingChanges > 0
                          ? i18n.tr("Save %1 change", "Save %1 changes", settingsTab.pendingChanges).arg(settingsTab.pendingChanges)
                          : i18n.tr("Save")
                    color: theme.palette.normal.positive
                    enabled: settingsTab.loaded && settingsTab.pendingChanges > 0
                             && settingsTab.allValid && !settingsTab.saving
                    onClicked: settingsTab.save()
                }
            }
        }
    }
}
