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
    property string appVersion: ""
    property string rawStatus: ""
    property bool settingsReady: false

    readonly property bool installed: ready && loadState !== "" && loadState !== "not-found"
    readonly property bool running: activeState === "active"
    readonly property bool enabledAtLogin: unitFileState === "enabled"

    function refresh() {
        if (!ready)
            return
        python.call("service_control.status", [], function(result) {
            var changed = result.LoadState !== loadState
                          || result.ActiveState !== activeState
                          || result.UnitFileState !== unitFileState
            loadState = result.LoadState
            activeState = result.ActiveState
            unitFileState = result.UnitFileState
            if (!installPromptShown && loadState === "not-found") {
                installPromptShown = true
                PopupUtils.open(installDialog)
            }
            if (changed)
                refreshRawStatus()
        })
    }

    function refreshRawStatus() {
        if (!ready)
            return
        python.call("service_control.raw_status", [], function(result) {
            rawStatus = result
        })
    }

    function callService(func, failMessage) {
        busy = true
        errorText = ""
        python.call("service_control." + func, [], function(result) {
            busy = false
            if (!result.ok)
                errorText = result.message !== "" ? result.message : failMessage
            refresh()
            refreshRawStatus()
        })
    }

    function installService() {
        callService("install", i18n.tr("Installing the service failed"))
    }

    function uninstallService() {
        callService("uninstall", i18n.tr("Uninstalling the service failed"))
    }

    function reinstallService() {
        callService("reinstall", i18n.tr("Reinstalling the service failed"))
    }

    function callPython(name, args, callback) {
        python.call(name, args, callback)
    }

    // After settings are written, restart the service if it's running so the daemon picks
    // them up. `what` starts the message ("Saved", "Defaults restored"); done(isError, message)
    function restartForSettings(what, done) {
        if (!(installed && running)) {
            done(false, installed
                 ? i18n.tr("%1. Glyphy isn't running, so the changes will apply when it starts.").arg(what)
                 : i18n.tr("%1. The changes will apply once the Glyphy service is installed and running.").arg(what))
            return
        }
        python.call("service_control.run", ["restart"], function(restart) {
            refresh()
            refreshRawStatus()
            done(!restart.ok, restart.ok
                 ? i18n.tr("%1, and Glyphy restarted to apply the changes.").arg(what)
                 : i18n.tr("%1, but restarting Glyphy failed: %2").arg(what).arg(restart.message))
        })
    }

    function confirmUninstall() {
        PopupUtils.open(uninstallDialog)
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
            refreshRawStatus()
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
            subtitle: root.appVersion !== "" ? i18n.tr("Version %1").arg(root.appVersion) : ""

            extension: Sections {
                id: sections
                anchors {
                    left: parent.left
                    leftMargin: units.gu(2)
                    bottom: parent.bottom
                }
                model: [i18n.tr("Settings"), i18n.tr("Advanced"),
                        i18n.tr("Service"), i18n.tr("About")]
            }
        }

        SettingsTab {
            anchors {
                top: header.bottom
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            visible: sections.selectedIndex === 0
            app: root
        }

        AdvancedTab {
            anchors {
                top: header.bottom
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            visible: sections.selectedIndex === 1
            app: root
        }

        ServiceTab {
            anchors {
                top: header.bottom
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            visible: sections.selectedIndex === 2
            app: root
        }

        AboutTab {
            anchors {
                top: header.bottom
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            visible: sections.selectedIndex === 3
            app: root
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

    Component {
        id: uninstallDialog

        Dialog {
            id: dialog
            title: i18n.tr("Uninstall the service?")
            text: i18n.tr("This stops Glyphy's background service, stops it from starting at login, and removes its unit file. You can install it again from here at any time.")

            Button {
                text: i18n.tr("Uninstall")
                color: theme.palette.normal.negative
                onClicked: {
                    PopupUtils.close(dialog)
                    root.uninstallService()
                }
            }
            Button {
                text: i18n.tr("Cancel")
                onClicked: PopupUtils.close(dialog)
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
                python.call("service_control.version", [], function(result) {
                    root.appVersion = result
                })
                root.refresh()
                root.refreshRawStatus()
            })
            importModule("settings_control", function() {
                root.settingsReady = true
            })
        }

        onError: {
            root.busy = false
            root.errorText = traceback
        }
    }
}
