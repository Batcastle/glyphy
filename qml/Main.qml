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
import io.thp.pyotherside 1.4

MainView {
    id: root
    objectName: "mainView"
    applicationName: "glyphy.batcastle"

    width: units.gu(45)
    height: units.gu(75)

    property bool ready: false
    property bool busy: false
    property string loadState: ""
    property string activeState: ""
    property string unitFileState: ""
    property string errorText: ""
    property bool installPromptShown: false

    readonly property bool installed: ready && loadState !== "" && loadState !== "not-found"
    readonly property bool running: activeState === "active"
    readonly property bool enabledAtLogin: unitFileState === "enabled"

    function refresh() {
        if (!ready)
            return
        python.call("service_control.status", [], function(result) {
            loadState = result.LoadState
            activeState = result.ActiveState
            unitFileState = result.UnitFileState
            if (!installPromptShown && loadState === "not-found") {
                installPromptShown = true
                PopupUtils.open(installDialog)
            }
        })
    }

    function installService() {
        busy = true
        errorText = ""
        python.call("service_control.install", [], function(result) {
            busy = false
            if (!result.ok)
                errorText = result.message !== "" ? result.message
                                                  : i18n.tr("Installing the service failed")
            refresh()
        })
    }

    function act(action) {
        busy = true
        errorText = ""
        python.call("service_control.run", [action], function(result) {
            busy = false
            if (!result.ok)
                errorText = result.message !== "" ? result.message
                                                  : i18n.tr("systemctl %1 failed").arg(action)
            refresh()
        })
    }

    function runningText() {
        if (!ready)
            return i18n.tr("Checking…")
        if (!installed)
            return i18n.tr("Not installed")
        switch (activeState) {
        case "active": return i18n.tr("Running")
        case "inactive": return i18n.tr("Stopped")
        case "failed": return i18n.tr("Failed")
        case "activating": return i18n.tr("Starting…")
        case "deactivating": return i18n.tr("Stopping…")
        default: return activeState
        }
    }

    function runningColor() {
        if (!installed || activeState === "failed")
            return theme.palette.normal.negative
        if (activeState === "active")
            return theme.palette.normal.positive
        if (activeState === "activating" || activeState === "deactivating")
            return theme.palette.normal.activity
        return theme.palette.normal.base
    }

    function enabledText() {
        if (!ready)
            return i18n.tr("Checking…")
        if (!installed)
            return i18n.tr("Not installed")
        switch (unitFileState) {
        case "enabled": return i18n.tr("Enabled")
        case "disabled": return i18n.tr("Disabled")
        case "masked": return i18n.tr("Masked")
        default: return unitFileState
        }
    }

    function enabledColor() {
        if (!installed || unitFileState === "masked")
            return theme.palette.normal.negative
        if (unitFileState === "enabled")
            return theme.palette.normal.positive
        return theme.palette.normal.base
    }

    Page {
        anchors.fill: parent

        header: PageHeader {
            id: header
            title: i18n.tr("Glyphy")
        }

        Flickable {
            anchors {
                top: header.bottom
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            contentHeight: content.height + units.gu(4)
            clip: true

            ColumnLayout {
                id: content
                anchors {
                    top: parent.top
                    left: parent.left
                    right: parent.right
                    margins: units.gu(2)
                }
                spacing: units.gu(2)

                Label {
                    text: i18n.tr("Service")
                    textSize: Label.Large
                    font.weight: Font.DemiBold
                }

                StatusRow {
                    label: i18n.tr("Status")
                    value: root.runningText()
                    indicatorColor: root.runningColor()
                }

                StatusRow {
                    label: i18n.tr("Start at login")
                    value: root.enabledText()
                    indicatorColor: root.enabledColor()
                }

                Label {
                    Layout.fillWidth: true
                    visible: root.ready && !root.installed
                    wrapMode: Text.Wrap
                    text: i18n.tr("The Glyphy service isn't installed, so it can't be controlled yet.")
                }

                Button {
                    Layout.fillWidth: true
                    visible: root.ready && !root.installed
                    text: i18n.tr("Install service")
                    color: theme.palette.normal.positive
                    enabled: !root.busy
                    onClicked: root.installService()
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: units.gu(1)

                    Button {
                        Layout.fillWidth: true
                        text: i18n.tr("Start")
                        color: theme.palette.normal.positive
                        enabled: root.installed && !root.busy && !root.running
                        onClicked: root.act("start")
                    }
                    Button {
                        Layout.fillWidth: true
                        text: i18n.tr("Stop")
                        color: theme.palette.normal.negative
                        enabled: root.installed && !root.busy && root.running
                        onClicked: root.act("stop")
                    }
                    Button {
                        Layout.fillWidth: true
                        text: i18n.tr("Restart")
                        enabled: root.installed && !root.busy
                        onClicked: root.act("restart")
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: units.gu(1)

                    Button {
                        Layout.fillWidth: true
                        text: i18n.tr("Enable")
                        enabled: root.installed && !root.busy && !root.enabledAtLogin
                        onClicked: root.act("enable")
                    }
                    Button {
                        Layout.fillWidth: true
                        text: i18n.tr("Disable")
                        enabled: root.installed && !root.busy && root.enabledAtLogin
                        onClicked: root.act("disable")
                    }
                }

                ActivityIndicator {
                    Layout.alignment: Qt.AlignHCenter
                    running: root.busy
                    visible: root.busy
                }

                Label {
                    Layout.fillWidth: true
                    visible: root.errorText !== ""
                    wrapMode: Text.Wrap
                    color: theme.palette.normal.negative
                    text: root.errorText
                }
            }
        }
    }

    Component {
        id: installDialog

        Dialog {
            id: dialog
            title: i18n.tr("Install the Glyphy service?")
            text: i18n.tr("Glyphy controls your glyph lights from a background service, and that service isn't installed yet. Installing it sets Glyphy to start automatically when you log in, and starts it now.")

            Button {
                text: i18n.tr("Yes")
                color: theme.palette.normal.positive
                onClicked: {
                    PopupUtils.close(dialog)
                    root.installService()
                }
            }
            Button {
                text: i18n.tr("No")
                onClicked: {
                    PopupUtils.close(dialog)
                    PopupUtils.open(declineDialog)
                }
            }
        }
    }

    Component {
        id: declineDialog

        Dialog {
            id: dialog
            title: i18n.tr("Are you sure about that?")
            text: i18n.tr("The service is what lets Glyphy start automatically when your phone boots. Without it, your glyph lights won't do anything until you start Glyphy's background process manually, and you'll have to do that again after every reboot.")

            Button {
                text: i18n.tr("Yes, I'm sure")
                onClicked: PopupUtils.close(dialog)
            }
            Button {
                text: i18n.tr("No, install it")
                color: theme.palette.normal.positive
                onClicked: {
                    PopupUtils.close(dialog)
                    root.installService()
                }
            }
        }
    }

    Timer {
        interval: 2000
        repeat: true
        running: root.ready && Qt.application.active
        onTriggered: root.refresh()
    }

    Python {
        id: python

        Component.onCompleted: {
            addImportPath(Qt.resolvedUrl("."))
            importModule("service_control", function() {
                root.ready = true
                root.refresh()
            })
        }

        onError: {
            root.busy = false
            root.errorText = traceback
        }
    }
}
