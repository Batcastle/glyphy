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

RowLayout {
    property alias label: nameLabel.text
    property alias value: valueLabel.text
    property color indicatorColor: theme.palette.normal.base

    Layout.fillWidth: true
    spacing: units.gu(1.5)

    Rectangle {
        Layout.preferredWidth: units.gu(1.5)
        Layout.preferredHeight: units.gu(1.5)
        Layout.alignment: Qt.AlignVCenter
        radius: width / 2
        color: indicatorColor
    }

    Label {
        id: nameLabel
        Layout.fillWidth: true
    }

    Label {
        id: valueLabel
        font.weight: Font.DemiBold
    }
}
