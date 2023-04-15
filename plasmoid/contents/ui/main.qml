import QtQuick 2.0
import QtQuick.Layouts 1.1
import org.kde.plasma.plasmoid 2.0
import org.kde.plasma.core 2.0 as PlasmaCore
import org.kde.plasma.components 3.0 as PlasmaComponents
import org.kde.plasma.extras 2.0 as PlasmaExtras

Item {
    id: root
    // Do never apply new values if one slider is not released yet
    property bool valuesLock: false

    // https://github.com/Zren/plasma-applet-commandoutput/blob/master/package/contents/ui/main.qml
    PlasmaCore.DataSource {
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
        }
        function exec(cmd) {
            if (cmd) {
                connectSource(cmd);
            }
        }
    }

    PlasmaCore.DataSource {
        id: monitorDataSource
        engine: "executable"
        connectedSources: []
        interval: 60 * 1000
        onNewData: function (cmd, data) {
            const exitCode = data["exit code"];
			const exitStatus = data["exit status"];
			const stdout = data.stdout;
			const stderr = data.stderr;

            if (cmd == oneoffCommand) {
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

        }
        readonly property string command: `${plasmoid.configuration.executable} detect`
        // add the meaningless variable `ONCE=1` in front so we can differentiate this one-off call from regular calls and disconnect it 
        readonly property string oneoffCommand: `ONCE=1 ${command}`
        function start() {
            connectSource(command);
        }
        function runOnce() {
            connectSource(oneoffCommand);
        }
        function stop() {
            disconnectSource(command);
        }
    }

    signal error(string message)
    function handleError(stdout, stderr) {
        try {
            const errorResponse = JSON.parse(stdout);
            console.log(`${errorResponse.command}: ${errorResponse.error}`);
            error(errorResponse.error);
        } catch(parse_error) {
            stdout = stdout.trim() ? ('\n    ' + stdout.trim()) : ''
            stderr = stderr.trim() ? ('\n    ' + stderr.trim()) : ''
            console.error('Error:' + stdout + stderr);
            error('Error:' + stdout + stderr);
        }
    }

    ListModel {
        id: monitorModel
    }

    Plasmoid.fullRepresentation: ColumnLayout {
        PlasmaExtras.PlasmoidHeading {
            leftPadding: PlasmaCore.Units.gridUnit / 4
            rightPadding: PlasmaCore.Units.gridUnit / 4
            RowLayout {
                anchors.fill: parent
                PlasmaExtras.Heading {
                    level: 1
                    text: 'Display Brightness'
                }

                PlasmaComponents.ToolButton {
                    Layout.alignment: Qt.AlignRight
                    icon.name: 'view-refresh-symbolic'
                    onClicked: monitorDataSource.runOnce()
                }
            }
        }

        ColumnLayout {
            Layout.leftMargin: PlasmaCore.Units.gridUnit / 2
            Layout.rightMargin: PlasmaCore.Units.gridUnit / 2
            Layout.bottomMargin: PlasmaCore.Units.gridUnit / 2

            RowLayout {
                id: error_layout

                visible: false
                Layout.minimumWidth: PlasmaCore.Units.gridUnit * 16
                spacing: PlasmaCore.Units.gridUnit

                PlasmaExtras.Paragraph {
                    id: error_text
                    Layout.fillWidth: true
                    color: PlasmaCore.Theme.negativeTextColor
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

            GridLayout {
                columns: 3
                rows: monitorModel.count
                flow: GridLayout.TopToBottom
                columnSpacing: PlasmaCore.Units.gridUnit / 2
                rowSpacing: PlasmaCore.Units.gridUnit / 2
                visible: monitorModel.count > 0

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
                        from: 0
                        to: 100
                        value: brightness
                        stepSize: plasmoid.configuration.stepSize || 1

                        onMoved: brightness = value
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
                        text: brightness + '%'
                    }
                }
            }
        }
    }

    Component.onCompleted: function() {
        monitorDataSource.start();
    }
}
