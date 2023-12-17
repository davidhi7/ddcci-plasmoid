import QtQuick 2.15
import QtQuick.Layouts 1.15

import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.extras as PlasmaExtras

PlasmoidItem {
    id: root
    // Do never apply new values if one slider is not released yet
    property bool valuesLock: false
    property bool outsideSysTray: !(plasmoid.containmentDisplayHints & PlasmaCore.Types.ContainmentDrawsPlasmoidHeading)

    // https://github.com/Zren/plasma-applet-commandoutput/blob/master/package/contents/ui/main.qml
    Plasma5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []
        onNewData: function (cmd, data) {
            const exitCode = data["exit code"];
			const exitStatus = data["exit status"];
			const stdout = data.stdout;
			const stderr = data.stderr;

            if (exitCode > 0) {
                handleError(stdout, stderr);
            }
			disconnectSource(cmd);

            // Auto close the error notifications
            commandSuccess(cmd);
        }
        function exec(cmd) {
            if (cmd) {
                connectSource(cmd);
            }
        }
    }

    Plasma5Support.DataSource {
        id: monitorDataSource
        engine: "executable"
        connectedSources: []
        interval: 60 * 1000
        onNewData: function (cmd, data) {
            const exitCode = data["exit code"];
			const exitStatus = data["exit status"];
			const stdout = data.stdout;
			const stderr = data.stderr;

            if (cmd === oneoffCommand) {
                disconnectSource(oneoffCommand);
            }

            if (exitCode > 0) {
                handleError(stdout, stderr)
                return;
            }

            // if the lock is held, simply do nothing and wait for the next refresh
            if (!valuesLock) {
                monitorModel.clear();
			    const response = JSON.parse(stdout);
                for (let instance of response.value) {
                    monitorModel.append(instance);
                }
            }

            commandSuccess(cmd);
        }
        property string command: `${plasmoid.configuration.executable} detect`
        // add the meaningless variable `ONCE=1` in front so we can differentiate this one-off call from regular calls and disconnect it 
        property string oneoffCommand: `ONCE=1 ${command}`
        function start() {
            connectSource(command);
        }
        function runOnce() {
            connectSource(oneoffCommand);
        }
        function stopAllCommands() {
            connectedSources.forEach(cmd =>{
                disconnectSource(cmd);
            })
        }
        function updateCommand() {
            command = `${plasmoid.configuration.executable} detect`;
            oneoffCommand = `ONCE=1 ${command}`;
        }
    }

    signal error(string message)
    signal commandSuccess(string cmd)
    function handleError(stdout, stderr) {
        try {
            const errorResponse = JSON.parse(stdout);
            console.log(`${errorResponse.command}: ${errorResponse.error}`);
            error(errorResponse.error);
        } catch(parse_error) {
            stdout = stdout.trim() ? ('\n    ' + stdout.trim()) : ''
            stderr = stderr.trim() ? ('\n    ' + stderr.trim()) : ''
            console.error('Error:' + stdout + stderr);
            error(i18n("Error:") + stdout + stderr);
        }
    }

    ListModel {
        id: monitorModel
    }

    fullRepresentation: ColumnLayout {
        PlasmaExtras.PlasmoidHeading {
            id: heading

            Layout.alignment: Qt.AlignTop

            // Don't render heading if this is part of the systemtray
            // Inside the systray, context menu options (like `refresh monitors`) are already rendered in the systray heading, so we don't need to do deal with this
            visible: root.outsideSysTray
            leftPadding: Kirigami.Units.smallSpacing
            rightPadding: Kirigami.Units.smallSpacing

            RowLayout {
                anchors.fill: parent

                PlasmaExtras.Heading {
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

            // Error notifications
            RowLayout {
                id: error_layout
                Layout.minimumWidth: Kirigami.Units.gridUnit * 16

                visible: false
                spacing: Kirigami.Units.gridUnit

                PlasmaComponents.Label {
                    id: error_text
                    Layout.fillWidth: true
                    color: Kirigami.Theme.negativeTextColor
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
                    commandSuccess.connect(function (_cmd) {
                        if (error_layout.visible) {
                            error_text.text = '';
                            error_layout.visible = false;
                        }
                    });
                }
            }

            // Fallback if no monitors detected
            PlasmaComponents.Label {
                visible: monitorModel.count === 0

                Layout.alignment: Qt.AlignHCenter
                text: i18n("No monitors detected")
            }

            // Main content
            GridLayout {
                visible: monitorModel.count > 0

                Layout.alignment: Qt.AlignHCenter
                columns: 3
                rows: monitorModel.count
                flow: GridLayout.TopToBottom
                columnSpacing: Kirigami.Units.gridUnit
                rowSpacing: Kirigami.Units.gridUnit

                Repeater {
                    model: monitorModel
                    delegate: PlasmaExtras.Heading {
                        level: 5
                        text: name
                    }
                }

                Repeater {
                    id: sliders
                    model: monitorModel
                    delegate: PlasmaComponents.Slider {
                        id: slider
                        // outside the systray, this causes layouting issues
                        Layout.fillWidth: !root.outsideSysTray
                        from: 0
                        to: 100
                        value: brightness
                        stepSize: plasmoid.configuration.stepSize || 1

                        Timer {
                            id: mouseWheelScrollingDebounceTimer

                            // How long does it take to trigger when the mouse wheel stops scrolling
                            interval: 400

                            // will only be triggered once after restart() called
                            repeat: false
                            running: false
                            triggeredOnStart: false

                            onTriggered: {
                                valuesLock = false
                                executable.exec(plasmoid.configuration.executable + ` set-brightness ${bus_id} ${brightness}`)
                            }
                        }

                        onMoved: () => {
                            // Should also be locked during mouse wheel scrolling.
                            valuesLock = true
                            brightness = value

                            // Handle mouse wheel debounce only when the slider is not pressed.
                            if (!pressed) {
                                mouseWheelScrollingDebounceTimer.restart()
                            }
                        }

                        onPressedChanged: function() {
                            if (pressed) {
                                valuesLock = true
                            } else {
                                // Slider is released
                                valuesLock = false
                                executable.exec(plasmoid.configuration.executable + ` set-brightness ${bus_id} ${brightness}`)
                            }
                        }
                    }
                }

                Repeater {
                    model: monitorModel
                    delegate: PlasmaComponents.Label {
                        id: percentageLabel
                        horizontalAlignment: Qt.AlignRight

                        text: brightness + '%'

                        Layout.minimumWidth: percentageMetrics.advanceWidth
                        TextMetrics {
                            id: percentageMetrics
                            font: percentageLabel.font
                            text: '100%'
                        }
                    }
                }
            }

            // Item to fill entire width and the remaining height, this way all other childs of the layout can be centered horizontally
            Item {
                height: 0
                Layout.fillWidth: true
                Layout.fillHeight: true
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

    Connections {
        target: plasmoid.configuration
        function onValueChanged(key, value) {
            if (key === 'executable') {
                monitorDataSource.stopAllCommands();
                monitorDataSource.updateCommand();
                monitorDataSource.start();
            }
        }
    }

    Component.onCompleted: function() {
        monitorDataSource.start();
    }
}
