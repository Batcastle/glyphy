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
import Lomiri.Components.Popups 1.3

// Advanced settings: everything in general.json except the "leds" mapping, built from what
// settings_control.general() reports, with a control chosen by each value's type.
// Changes are staged here and only written when Save is pressed.
Item {
    id: advancedTab
    property var app

    readonly property bool ready: app ? app.settingsReady : false
    property bool loaded: false
    property bool saving: false
    property int pendingChanges: 0
    property bool allValid: true
    property string message: ""
    property bool messageIsError: false
    property var ledNames: []

    // Settings that can stop Glyphy from controlling the lights if they're wrong
    readonly property var riskyKeys: ["base", "max_brightness", "min_brightness"]

    function tidy(name) {
        var words = name.replace(/_/g, " ")
        return words.charAt(0).toUpperCase() + words.slice(1)
    }

    function listOf(text) {
        return text === "" ? [] : text.split(",")
    }

    function setLed(row, name, checked) {
        var current = listOf(fieldModel.get(row).value)
        var updated = []
        for (var i = 0; i < ledNames.length; i++) {
            var led = ledNames[i]
            if (led === name ? checked : current.indexOf(led) >= 0)
                updated.push(led)
        }
        fieldModel.setProperty(row, "value", updated.join(","))
        countChanges()
    }

    function fieldValid(row) {
        var text = row.value
        switch (row.kind) {
        case "int":
            if (!/^[0-9]+$/.test(text))
                return false
            break
        case "float":
            if (!/^[0-9]*\.?[0-9]+$/.test(text))
                return false
            break
        case "string":
            return text.trim() !== ""
        case "leds":
            return listOf(text).length > 0
        default:
            return true
        }
        // A frequency of 0 would make the daemon divide by zero
        return !(/_frequency$/.test(row.key) && parseFloat(text) <= 0)
    }

    function typedValue(row) {
        switch (row.kind) {
        case "bool": return row.value === "true"
        case "int": return parseInt(row.value)
        case "float": return parseFloat(row.value)
        case "leds": return listOf(row.value)
        case "list": return listOf(row.value).map(function(item) { return item.trim() })
        default: return row.value
        }
    }

    function countChanges() {
        var count = 0
        var valid = true
        for (var i = 0; i < fieldModel.count; i++) {
            var row = fieldModel.get(i)
            if (row.value !== row.savedValue)
                count++
            if (!fieldValid(row))
                valid = false
        }
        pendingChanges = count
        allValid = valid
    }

    function load() {
        app.callPython("settings_control.general", [], function(result) {
            ledNames = result.leds
            fieldModel.clear()
            var lastSection = null
            for (var i = 0; i < result.fields.length; i++) {
                var field = result.fields[i]
                var section = field.path.length > 1 ? field.path[0] : ""
                var value = Array.isArray(field.value) ? field.value.join(",") : String(field.value)
                var key = field.path[field.path.length - 1]
                fieldModel.append({
                    "path": JSON.stringify(field.path), "section": section, "key": key,
                    "kind": field.kind, "value": value, "savedValue": value,
                    "showHeader": section !== lastSection && section !== "",
                    "risky": riskyKeys.indexOf(key) >= 0
                })
                lastSection = section
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
        for (var i = 0; i < fieldModel.count; i++)
            fieldModel.setProperty(i, "value", fieldModel.get(i).savedValue)
        message = ""
        countChanges()
    }

    function save() {
        var changes = {}
        for (var i = 0; i < fieldModel.count; i++) {
            var row = fieldModel.get(i)
            if (row.value === row.savedValue)
                continue
            // Rebuild the nesting from the field's path, e.g. ["general", "base"]
            var path = JSON.parse(row.path)
            var node = changes
            for (var p = 0; p < path.length - 1; p++) {
                if (node[path[p]] === undefined)
                    node[path[p]] = {}
                node = node[path[p]]
            }
            node[path[path.length - 1]] = typedValue(row)
        }
        saving = true
        message = ""
        app.callPython("settings_control.save", [{"general.json": changes}], function(result) {
            if (!result.ok) {
                saving = false
                message = result.message
                messageIsError = true
                return
            }
            for (var j = 0; j < fieldModel.count; j++)
                fieldModel.setProperty(j, "savedValue", fieldModel.get(j).value)
            countChanges()
            app.restartForSettings(i18n.tr("Saved"), function(isError, text) {
                saving = false
                messageIsError = isError
                message = text
            })
        })
    }

    function restoreDefaults() {
        saving = true
        message = ""
        app.callPython("settings_control.reset", ["general.json"], function(result) {
            if (!result.ok) {
                saving = false
                message = result.message
                messageIsError = true
                return
            }
            load()
            app.restartForSettings(i18n.tr("Defaults restored"), function(isError, text) {
                saving = false
                messageIsError = isError
                message = text
            })
        })
    }

    onReadyChanged: if (ready) load()

    ListModel {
        id: fieldModel
    }

    Component {
        id: restoreDialog

        Dialog {
            id: dialog
            title: i18n.tr("Restore default advanced settings?")
            text: i18n.tr("This undoes every change made on this page and restarts Glyphy if it's running.")

            Button {
                text: i18n.tr("Restore defaults")
                color: theme.palette.normal.negative
                onClicked: {
                    PopupUtils.close(dialog)
                    advancedTab.restoreDefaults()
                }
            }
            Button {
                text: i18n.tr("Cancel")
                onClicked: PopupUtils.close(dialog)
            }
        }
    }

    Flickable {
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            bottom: saveBar.top
        }
        contentHeight: column.height + units.gu(2)
        clip: true

        ColumnLayout {
            id: column
            anchors {
                top: parent.top
                left: parent.left
                right: parent.right
                margins: units.gu(2)
            }
            spacing: units.gu(1.5)

            Label {
                text: i18n.tr("Advanced Settings")
                textSize: Label.Large
                font.weight: Font.DemiBold
            }

            // Warning about the settings that can break light control
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: warningLabel.height + units.gu(3)
                radius: units.gu(1)
                color: "transparent"
                border.width: units.dp(2)
                border.color: theme.palette.normal.negative

                Label {
                    id: warningLabel
                    anchors {
                        left: parent.left
                        right: parent.right
                        verticalCenter: parent.verticalCenter
                        margins: units.gu(1.5)
                    }
                    wrapMode: Text.Wrap
                    text: i18n.tr("Don't change %1, %2, or %3 unless you know what you're doing. Wrong values can stop Glyphy from controlling your lights.")
                          .arg(advancedTab.tidy("base")).arg(advancedTab.tidy("max_brightness"))
                          .arg(advancedTab.tidy("min_brightness"))
                }
            }

            Repeater {
                model: fieldModel

                delegate: ColumnLayout {
                    id: fieldItem
                    Layout.fillWidth: true
                    spacing: units.gu(1)
                    enabled: !advancedTab.saving

                    readonly property int row: index
                    readonly property string fieldValue: model.value

                    Label {
                        visible: model.showHeader
                        Layout.topMargin: units.gu(1)
                        text: advancedTab.tidy(model.section)
                        textSize: Label.Large
                        font.weight: Font.DemiBold
                    }

                    // On/off values
                    RowLayout {
                        visible: model.kind === "bool"
                        Layout.fillWidth: true

                        Label {
                            Layout.fillWidth: true
                            wrapMode: Text.Wrap
                            text: advancedTab.tidy(model.key)
                        }
                        Switch {
                            checked: fieldItem.fieldValue === "true"
                            onCheckedChanged: {
                                var text = checked ? "true" : "false"
                                if (text !== fieldItem.fieldValue) {
                                    fieldModel.setProperty(fieldItem.row, "value", text)
                                    advancedTab.countChanges()
                                }
                            }
                        }
                    }

                    // Numbers, text, and plain lists
                    Label {
                        visible: model.kind !== "bool"
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                        color: model.risky ? theme.palette.normal.negative : theme.palette.normal.backgroundText
                        text: model.risky ? i18n.tr("%1 (change with care)").arg(advancedTab.tidy(model.key))
                                          : advancedTab.tidy(model.key)
                    }
                    TextField {
                        visible: ["int", "float", "string", "list"].indexOf(model.kind) >= 0
                        Layout.fillWidth: true
                        text: fieldItem.fieldValue
                        hasClearButton: false
                        errorHighlight: true
                        inputMethodHints: model.kind === "int" ? Qt.ImhDigitsOnly
                                        : model.kind === "float" ? Qt.ImhFormattedNumbersOnly
                                        : Qt.ImhNoPredictiveText
                        validator: RegExpValidator {
                            regExp: model.kind === "int" ? /^[0-9]*$/
                                  : model.kind === "float" ? /^[0-9]*\.?[0-9]*$/
                                  : /.*/
                        }
                        onTextChanged: {
                            if (text !== fieldItem.fieldValue) {
                                fieldModel.setProperty(fieldItem.row, "value", text)
                                advancedTab.countChanges()
                            }
                        }
                    }

                    // Lists of LEDs, e.g. which LEDs "all" means
                    Flow {
                        visible: model.kind === "leds"
                        Layout.fillWidth: true
                        spacing: units.gu(2)

                        Repeater {
                            model: advancedTab.ledNames

                            delegate: Row {
                                spacing: units.gu(1)

                                CheckBox {
                                    anchors.verticalCenter: parent.verticalCenter
                                    checked: advancedTab.listOf(fieldItem.fieldValue).indexOf(modelData) >= 0
                                    onClicked: advancedTab.setLed(fieldItem.row, modelData, checked)
                                }
                                Label {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: advancedTab.tidy(modelData)
                                }
                            }
                        }
                    }
                }
            }

            Button {
                Layout.fillWidth: true
                Layout.topMargin: units.gu(2)
                visible: advancedTab.loaded
                text: i18n.tr("Restore defaults")
                enabled: !advancedTab.saving
                onClicked: PopupUtils.open(restoreDialog)
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
                visible: advancedTab.message !== "" || !advancedTab.allValid
                wrapMode: Text.Wrap
                color: (advancedTab.messageIsError || !advancedTab.allValid)
                       ? theme.palette.normal.negative
                       : theme.palette.normal.backgroundSecondaryText
                text: !advancedTab.allValid ? i18n.tr("Some settings need fixing before you can save.")
                                            : advancedTab.message
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: units.gu(1)

                ActivityIndicator {
                    running: advancedTab.saving
                    visible: advancedTab.saving
                }

                Button {
                    visible: advancedTab.pendingChanges > 0 || !advancedTab.allValid
                    text: i18n.tr("Discard")
                    enabled: !advancedTab.saving
                    onClicked: advancedTab.discard()
                }

                Button {
                    Layout.fillWidth: true
                    text: advancedTab.pendingChanges > 0
                          ? i18n.tr("Save %1 change", "Save %1 changes", advancedTab.pendingChanges).arg(advancedTab.pendingChanges)
                          : i18n.tr("Save")
                    color: theme.palette.normal.positive
                    enabled: advancedTab.loaded && advancedTab.pendingChanges > 0
                             && advancedTab.allValid && !advancedTab.saving
                    onClicked: advancedTab.save()
                }
            }
        }
    }
}
