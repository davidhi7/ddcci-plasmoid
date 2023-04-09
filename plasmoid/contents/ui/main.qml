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
			exited(cmd, exitCode, exitStatus, stdout, stderr);
			disconnectSource(cmd);
        }
        function exec(cmd) {
            if (cmd) {
                connectSource(cmd);
            }
        }
        signal exited(string cmd, int exitCode, int exitStatus, string stdout, string stderr)
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
            if (exitCode > 1) {
                console.log('Failed to fetch monitor data');
                return;
            }

			const response = JSON.parse(stdout);
            // if the lock is held, simply do nothing and wait for the next refresh
            if (response.command === 'detect' && !valuesLock) {
                monitorModel.clear();
                for (let instance of response.value) {
                    monitorModel.append(instance);
                }
            }
        }
        readonly property string command: plasmoid.configuration.executable + ' detect'
        function start() {
            connectSource(command);
        }
        function stop() {
            disconnectSource(command);
        }
    }

    ListModel {
        id: monitorModel
    }

    Plasmoid.fullRepresentation: ColumnLayout {
        id: fullRep

        PlasmaExtras.PlasmoidHeading {
            PlasmaExtras.Heading {
                level: 1
                text: 'Display Brightness'
            }
        }

        GridLayout {
            columns: 3
            rows: monitorModel.count
            flow: GridLayout.TopToBottom
            columnSpacing: PlasmaCore.Units.gridUnit / 2
            rowSpacing: PlasmaCore.Units.gridUnit / 2
            Layout.margins: PlasmaCore.Units.gridUnit / 2

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

    Component.onCompleted: function() {
    //     executable.exited.connect(function(cmd, exitCode, exitStatus, stdout, stderr) {
    //         console.log(stdout, stderr);
    //         if (stdout) {
    //             const response = JSON.parse(stdout);
    //             // TODO handle
    //         }
    //     });

        monitorDataSource.start();
    }
}
