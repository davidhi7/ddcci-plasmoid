import QtQuick
import QtQuick.Layouts

import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.plasma5support as Plasma5Support

import org.kde.kirigami as Kirigami

import "code/backend_interface.js" as Backend

PlasmoidItem {
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
    Plasma5Support.DataSource {
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

    fullRepresentation: ColumnLayout {
        PlasmaExtras.PlasmoidHeading {
            id: heading
            // Don't render heading if this is part of the systemtray
            // Inside the systray, actions (like refresh monitors) are already rendered in the systray heading, so we don't need to do deal with this
            visible: root.outsideSysTray


            Layout.alignment: Qt.AlignTop
            leftPadding: Kirigami.Units.smallSpacing
            rightPadding: Kirigami.Units.smallSpacing

            RowLayout {
                anchors.fill: parent

                Kirigami.Heading {
                    level: 1
                    text: i18n("Display Brightness")
                }

                PlasmaComponents.ToolButton {
                    Layout.alignment: Qt.AlignRight

                    // Using `action` fails
                    property QtObject /*Plasmacore.Action*/ action_: Plasmoid.contextualActions[0]

                    icon.name: action_.icon.name
                    PlasmaComponents.ToolTip {
                        text: parent.action_.text
                    }
                    onClicked: action_.trigger()
                }
            }
        }

        ColumnLayout {
            Layout.margins: Kirigami.Units.gridUnit

            Kirigami.InlineMessage {
                id: errorMessage

                Layout.fillWidth: true
                visible: false
                type: Kirigami.MessageType.Error
                showCloseButton: true

                Component.onCompleted: function() {
                    error.connect(function (message) {
                        errorMessage.text = message;
                        errorMessage.visible = true;
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

                Item {
                    height: 0
                    Layout.fillWidth: true
                }
            }

        }
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

    Plasmoid.contextualActions: [
        PlasmaCore.Action {
            text: i18n("Refresh monitors")
            icon.name: "view-refresh-symbolic"
            onTriggered: monitorDataSource.runOnce();
        }
    ]

    Component.onCompleted: function() {
        executable.exec(`${backendCommand} version`, (exitCode, stdout, stderr) => {
            log(`Backend version: ${removeTrailingNewlines(stdout)}`);
        });
        monitorDataSource.start();
        write_backend_configuration();
    }
}
