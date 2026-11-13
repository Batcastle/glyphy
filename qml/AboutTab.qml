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

// About Glyphy: logo, version, license, credits, and project links
Item {
    id: aboutTab
    property var app

    readonly property string repoUrl: "https://github.com/Batcastle/Glyphy"

    Flickable {
        anchors.fill: parent
        contentHeight: content.height + units.gu(6)
        clip: true

        ColumnLayout {
            id: content
            anchors {
                top: parent.top
                left: parent.left
                right: parent.right
                topMargin: units.gu(4)
                leftMargin: units.gu(3)
                rightMargin: units.gu(3)
            }
            spacing: units.gu(2)

            Image {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: units.gu(14)
                Layout.preferredHeight: units.gu(14)
                source: Qt.resolvedUrl("../assets/logo.svg")
                sourceSize.width: units.gu(14)
                sourceSize.height: units.gu(14)
                fillMode: Image.PreserveAspectFit
            }

            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: "Glyphy"
                textSize: Label.XLarge
                font.weight: Font.DemiBold
            }

            Label {
                Layout.fillWidth: true
                Layout.topMargin: -units.gu(1.5)
                horizontalAlignment: Text.AlignHCenter
                visible: aboutTab.app && aboutTab.app.appVersion !== ""
                text: aboutTab.app ? i18n.tr("Version %1").arg(aboutTab.app.appVersion) : ""
                color: theme.palette.normal.backgroundSecondaryText
            }

            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                text: i18n.tr("Glyphy brings the Glyph lights on the back of your Nothing Phone (1) to life on Ubuntu Touch, with animations for notifications, charging, video recording, and more.")
            }

            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                text: i18n.tr("Glyphy is free software, released under the GNU General Public License, version 3.")
            }

            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
                text: i18n.tr("Created by Thomas Castleman, with help from Claude Opus 5.5.")
            }

            Button {
                Layout.fillWidth: true
                Layout.topMargin: units.gu(1)
                text: i18n.tr("View on GitHub")
                onClicked: Qt.openUrlExternally(aboutTab.repoUrl)
            }

            Button {
                Layout.fillWidth: true
                text: i18n.tr("Report an issue")
                onClicked: Qt.openUrlExternally(aboutTab.repoUrl + "/issues")
            }
        }
    }
}
