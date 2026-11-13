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

// Service status and controls. All state and actions live in Main.qml (passed in as `app`).
Item {
    id: serviceTab
    property var app

    Flickable {
        anchors.fill: parent
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
                value: app.runningText()
                indicatorColor: app.runningColor()
            }

            StatusRow {
                label: i18n.tr("Start at login")
                value: app.enabledText()
                indicatorColor: app.enabledColor()
            }

            Label {
                Layout.fillWidth: true
                visible: app.ready && !app.installed
                wrapMode: Text.Wrap
                text: i18n.tr("The Glyphy service isn't installed, so it can't be controlled yet.")
            }

            Button {
                Layout.fillWidth: true
                visible: app.ready && !app.installed
                text: i18n.tr("Install service")
                color: theme.palette.normal.positive
                enabled: !app.busy
                onClicked: app.installService()
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: units.gu(1)

                Button {
                    Layout.fillWidth: true
                    text: i18n.tr("Start")
                    color: theme.palette.normal.positive
                    enabled: app.installed && !app.busy && !app.running
                    onClicked: app.act("start")
                }
                Button {
                    Layout.fillWidth: true
                    text: i18n.tr("Stop")
                    color: theme.palette.normal.negative
                    enabled: app.installed && !app.busy && app.running
                    onClicked: app.act("stop")
                }
                Button {
                    Layout.fillWidth: true
                    text: i18n.tr("Restart")
                    enabled: app.installed && !app.busy
                    onClicked: app.act("restart")
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: units.gu(1)

                Button {
                    Layout.fillWidth: true
                    text: i18n.tr("Enable")
                    enabled: app.installed && !app.busy && !app.enabledAtLogin
                    onClicked: app.act("enable")
                }
                Button {
                    Layout.fillWidth: true
                    text: i18n.tr("Disable")
                    enabled: app.installed && !app.busy && app.enabledAtLogin
                    onClicked: app.act("disable")
                }
            }

            ActivityIndicator {
                Layout.alignment: Qt.AlignHCenter
                running: app.busy
                visible: app.busy
            }

            Label {
                Layout.fillWidth: true
                visible: app.errorText !== ""
                wrapMode: Text.Wrap
                color: theme.palette.normal.negative
                text: app.errorText
            }

            Label {
                visible: app.installed
                text: i18n.tr("Service file")
                textSize: Label.Large
                font.weight: Font.DemiBold
            }

            RowLayout {
                Layout.fillWidth: true
                visible: app.installed
                spacing: units.gu(1)

                Button {
                    Layout.fillWidth: true
                    text: i18n.tr("Reinstall")
                    enabled: !app.busy
                    onClicked: app.reinstallService()
                }
                Button {
                    Layout.fillWidth: true
                    text: i18n.tr("Uninstall")
                    color: theme.palette.normal.negative
                    enabled: !app.busy
                    onClicked: app.confirmUninstall()
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: units.gu(1)

                Label {
                    Layout.fillWidth: true
                    text: i18n.tr("systemd status")
                    textSize: Label.Large
                    font.weight: Font.DemiBold
                }
                Button {
                    text: i18n.tr("Refresh")
                    enabled: app.ready
                    onClicked: app.refreshRawStatus()
                }
            }

            TextArea {
                Layout.fillWidth: true
                Layout.preferredHeight: units.gu(30)
                readOnly: true
                selectByMouse: true
                wrapMode: TextEdit.WrapAnywhere
                font.family: "Ubuntu Mono"
                textFormat: TextEdit.PlainText
                text: app.rawStatus
            }

        }
    }
}
