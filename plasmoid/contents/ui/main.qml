import QtQuick 2.15
import QtQuick.Layouts 1.15

import org.kde.plasma.plasmoid 2.0
import org.kde.plasma.core 2.0 as PlasmaCore
import org.kde.plasma.components 3.0 as PlasmaComponents
import org.kde.plasma.extras 2.0 as PlasmaExtras

import org.kde.kirigami 2.20 as Kirigami

import "code/backend_interface.js" as Backend

Item {
    id: root
    // --- Global variables ---
    // Enable or disable debug logging
    readonly property bool enableLogging: true
    // Command to invoke the backend program
    property string backendCommand: plasmoid.configuration.executable
    // Interface to call the backend to set new properties
    property var backendInstance: new Backend.BackendInterface(executable, backendCommand)


    // Do never apply new values if one slider is not released yet
    property bool valuesLock: false
    property bool outsideSysTray: !(plasmoid.containmentDisplayHints & PlasmaCore.Types.ContainmentDrawsPlasmoidHeading)

    function log(message) {
        if (plasmoid.configuration.general_enable_logging) {
            console.log(`LOGGING: ${message}`);
            if (plasmoid.configuration.general_log_file !== "") {
                console.log(plasmoid.configuration.general_log_file)
                executable.exec(`echo "${message}" >> "${plasmoid.configuration.general_log_file}"`);
            }
        }
    }

    function removeTrailingNewlines(arg) {
        return arg.replace(/\n$/, '');
    }

    // Executable DataSource for all commands but regular backend polling
    ShellDataSource {
        id: executable
    }

    // DataSource for regular backend polling
    // TODO error handling
    PlasmaCore.DataSource {
        id: monitorDataSource
        engine: "executable"
        connectedSources: []
        interval: 60 * 1000
        onNewData: function (command, data) {
            const exitCode = data["exit code"];
			const exitStatus = data["exit status"];
			const stdout = data.stdout;
			const stderr = data.stderr;

            if (command === oneoffCommand) {
                disconnectSource(oneoffCommand);
            }

            if (exitCode > 0) {
                handleError(stdout, stderr);
                return;
            }

            // if the lock is held, simply do nothing and wait for the next refresh
            // TODO also look if latest ddcutil setvcp call is newer happened before current detect call
            if (!valuesLock) {
                monitorModel.clear();
			    const output = JSON.parse(stdout);
                for (let adapter in output.response) {
                    for (let id in output.response[adapter]) {
                        let monitor = output.response[adapter][id];
                        monitor.id = id;
                        monitor.adapter = adapter;
                        monitorModel.append(monitor);
                    }
                }
            }
        }
        // Command to query monitor data
        property string pollingCommand: `${backendCommand} detect ddcci`
        // Add the meaningless variable `ONCE=1` in front so we can differentiate this one-off call from regular calls and disconnect it 
        property string oneoffCommand: `ONCE=1 ${pollingCommand}`
        function start() {
            log(`Start backend detect polling with command '${pollingCommand}'`);
            connectSource(pollingCommand);
        }
        function runOnce() {
            log(`Run backend detect once with command '${oneoffCommand}'`);
            connectSource(oneoffCommand);
        }
        function restart() {
            connectedSources = []
            log(`Restart backup detect polling with command '${pollingCommand}'`);
            connectSource(pollingCommand);
        }
        onPollingCommandChanged: {
            restart();
        }
    }

    signal error(string message)
    function handleError(stdout, stderr) {
        try {
            const errorResponse = JSON.parse(stdout);
            log(`${errorResponse.command}: ${errorResponse.error}`);
            error(errorResponse.error);
        } catch(parse_error) {
            stdout = stdout.trim() ? ('\n    ' + stdout.trim()) : ''
            stderr = stderr.trim() ? ('\n    ' + stderr.trim()) : ''
            log('Error:' + stdout + stderr);
            error(i18n("Error:") + stdout + stderr);
        }
    }

    ListModel {
        id: monitorModel
    }

    Plasmoid.fullRepresentation: ColumnLayout {
        PlasmaExtras.PlasmoidHeading {
            id: heading
            // Don't render heading if this is part of the systemtray
            // Inside the systray, context menu options (like `refresh monitors`) are already rendered in the systray heading, so we don't need to do deal with this
            visible: root.outsideSysTray


            Layout.alignment: Qt.AlignTop
            leftPadding: PlasmaCore.Units.smallSpacing
            rightPadding: PlasmaCore.Units.smallSpacing

            RowLayout {
                anchors.fill: parent

                PlasmaExtras.Heading {
                    level: 1
                    text: i18n("Display Brightness")
                }

                PlasmaComponents.ToolButton {
                    Layout.alignment: Qt.AlignRight

                    property QtObject /*QAction*/ qAction: Plasmoid.action('refreshMonitors')

                    icon.name: 'view-refresh-symbolic'
                    PlasmaComponents.ToolTip {
                        text: parent.qAction.text
                    }
                    onClicked: qAction.trigger()
                }
            }
        }

        ColumnLayout {
            Layout.margins: PlasmaCore.Units.gridUnit

            // Error notifications
            RowLayout {
                id: error_layout
                Layout.minimumWidth: PlasmaCore.Units.gridUnit * 16

                visible: false
                spacing: PlasmaCore.Units.gridUnit

                PlasmaComponents.Label {
                    id: error_text
                    Layout.fillWidth: true
                    color: PlasmaCore.Theme.negativeTextColor
                    wrapMode: Text.WordWrap
                    font.bold: true
                }

                PlasmaComponents.ToolButton {
                    Layout.alignment: Qt.AlignRight
                    icon.name: 'window-close'
                    onClicked: error_layout.visible = false
                }

                Component.onCompleted: function() {
                    error.connect(function (message) {
                        error_text.text = message;
                        error_layout.visible = true;
                    });
                }
            }

            // Fallback if no monitors detected
            PlasmaComponents.Label {
                visible: monitorModel.count === 0

                Layout.alignment: Qt.AlignHCenter
                text: i18n("No monitors detected")
            }

            ColumnLayout {
                Repeater {
                    model: monitorModel
                    delegate: AdvancedMonitorItem {
                        visible: plasmoid.configuration.enableAdvancedMode
                        backendWrapper: backendInstance 
                    }
                }

                Repeater {
                    model: monitorModel
                    delegate: SimpleMonitorItem {
                        visible: !plasmoid.configuration.enableAdvancedMode
                        backendWrapper: backendInstance 
                    }
                }

                // TODO: why is this not working?
                // Repeater {
                //     model: monitorModel
                //     delegate: plasmoid.configuration.enableAdvancedMode ? AdvancedMonitorItem {} : SimpleMonitorItem {}
                // }

                Item {
                    height: 0
                    Layout.fillWidth: true
                }
            }

        }
    }

    // Handle `refresh monitors` button
    function action_refreshMonitors() {
        monitorDataSource.runOnce();
    }

    // Write the plasmoid configuration to the backend
    function write_backend_configuration() {
        for (let key in plasmoid.configuration) {
            if (key.startsWith("ddcci_") && !key.endsWith("Default")) {
                let [ config_section ] = key.split("_", 1);
                // Remove the leading `section_` part of key
                let config_key = key.substr(config_section.length + 1);
                executable.exec(`${backendCommand} config ${config_section} ${config_key} ${plasmoid.configuration[key]}`);
            }
        }
    }

    Component.onCompleted: function() {
        executable.exec(`${backendCommand} version`, (exitCode, stdout, stderr) => {
            log(`Backend version: ${removeTrailingNewlines(stdout)}`);
        });
        monitorDataSource.start();
        // code to add new action: Plasmoid.setAction("actionId", i18_n("text"), "iconName") (i18_n without underscore)
        // Instead of connecting to a signal of this action, a function called `action_{actionId}` is expected (here action_refreshMonitors)
        Plasmoid.setAction('refreshMonitors', i18n("Refresh monitors"), 'view-refresh-symbolic');

        write_backend_configuration();
    }
}
