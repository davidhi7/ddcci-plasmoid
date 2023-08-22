import QtQuick 2.15
import QtQuick.Layouts 1.15

import org.kde.plasma.plasmoid 2.0
import org.kde.plasma.core 2.0 as PlasmaCore
import org.kde.plasma.components 3.0 as PlasmaComponents
import org.kde.plasma.extras 2.0 as PlasmaExtras

Item {
    id: root
    // Do never apply new values if one slider is not released yet
    property bool valuesLock: false
    property bool outsideSysTray: !(plasmoid.containmentDisplayHints & PlasmaCore.Types.ContainmentDrawsPlasmoidHeading)

    Connections {
        target: valuesLock
        onChanged: () => {
            console.log(valuesLock)
        } 
    }

    // https://github.com/Zren/plasma-applet-commandoutput/blob/master/package/contents/ui/main.qml
    // PlasmaCore.DataSource {
    //     id: executable
    //     engine: "executable"
    //     connectedSources: []
    //     onNewData: function (cmd, data) {
    //         const exitCode = data["exit code"];
	// 		const exitStatus = data["exit status"];
	// 		const stdout = data.stdout;
	// 		const stderr = data.stderr;

    //         if (exitCode > 0) {
    //             handleError(stdout, stderr);
    //         }
	// 		disconnectSource(cmd);
    //     }
    //     function exec(cmd) {
    //         if (cmd) {
    //             connectSource(cmd);
    //         }
    //     }
    // }

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

            if (cmd === oneoffCommand) {
                disconnectSource(oneoffCommand);
            }

            if (exitCode > 0) {
                handleError(stdout, stderr);
                return;
            }

            // if the lock is held, simply do nothing and wait for the next refresh
            // if (!valuesLock) {
            if (true) {
                monitorModel.clear();
			    const response = JSON.parse(stdout);
                for (let adapter in response.response) {
                    // TODO do take adapters into account
                    for (let key in response.response[adapter]) {
                        monitorModel.append(response.response[adapter][key]);
                    }
                }
            }
        }
        // readonly property string command: `${plasmoid.configuration.executable} detect`
        readonly property string command: `${plasmoid.configuration.executable}`
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
                    // visible: plasmoid.configuration.enableAdvancedMode
                    model: monitorModel
                    delegate: AdvancedMonitorItem {
                        visible: plasmoid.configuration.enableAdvancedMode
                    }
                }

                Repeater {
                    model: monitorModel
                    delegate: SimpleMonitorItem {
                        visible: !plasmoid.configuration.enableAdvancedMode
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
                    // Layout.fillHeight: true
                }
            }

            // Main content
            // GridLayout {
            //     visible: monitorModel.count > 0

            //     Layout.alignment: Qt.AlignHCenter
            //     columns: 2
            //     rows: monitorModel.count
            //     flow: GridLayout.TopToBottom
            //     columnSpacing: PlasmaCore.Units.gridUnit / 2
            //     rowSpacing: PlasmaCore.Units.gridUnit

            //     Repeater {
            //         model: monitorModel
            //         delegate: ColumnLayout {
            //             spacing: 0
            //             PlasmaComponents.Label {
            //                 Layout.alignment: Qt.AlignRight
            //                 Layout.rightMargin: 4
                            
            //                 // level: 5
            //                 text: name
            //             }
            //             PlasmaComponents.ToolButton {         
            //                 visible:  plasmoid.configuration.advancedMode                   
            //                 Layout.alignment: Qt.AlignRight
            //                 icon.name: 'system-shutdown-symbolic'
            //                 PlasmaComponents.ToolTip {
            //                     text: 'Shut monitors down'
            //                 }
            //                 icon {
            //                     width: 16
            //                     height: 16
            //                 }
            //             }
            //             Item {
            //                 Layout.fillWidth: true
            //             }
            //         }
            //     }

            //     Repeater {
            //         model: monitorModel
            //         delegate: ColumnLayout {
            //             RowLayout {
            //                 Layout.alignment: Qt.AlignRight
            //                 PlasmaComponents.Label {
            //                     visible:  plasmoid.configuration.advancedMode
            //                     Layout.alignment: Qt.AlignRight
            //                     Layout.rightMargin: 4
            //                     text: 'Brightness:'
            //                 }

            //                 PlasmaComponents.Slider {
            //                     id: brightnessSlider
            //                     Layout.fillWidth: !root.outsideSysTray
            //                     from: 0
            //                     to: 100
            //                     value: brightness
            //                 }

            //                 PlasmaComponents.Label {
            //                     id: percentageLabel
            //                     horizontalAlignment: Qt.AlignRight

            //                     text: brightness + '%'
            //                     Layout.minimumWidth: percentageMetrics.advanceWidth
            //                 }
            //             }

            //             RowLayout {
            //                 visible:  plasmoid.configuration.advancedMode
            //                 Layout.alignment: Qt.AlignRight
            //                 PlasmaComponents.Label {
            //                     Layout.alignment: Qt.AlignRight
            //                     Layout.rightMargin: 4
            //                     text: 'Contrast:'
            //                 }

            //                 PlasmaComponents.Slider {
            //                     id: contrastSlider
            //                     Layout.fillWidth: !root.outsideSysTray
            //                     from: 0
            //                     to: 100
            //                     value: brightness
            //                 }

            //                 PlasmaComponents.Label {
            //                     horizontalAlignment: Qt.AlignRight

            //                     text: brightness + '%'
            //                     Layout.minimumWidth: percentageMetrics.advanceWidth
            //                 }
            //             }
            //         }
            //     }

            //         // delegate: PlasmaComponents.Slider {
            //         //     id: slider
            //         //     // outside the systray, this causes layouting issues
            //         //     Layout.fillWidth: !root.outsideSysTray
            //         //     from: 0
            //         //     to: 100
            //         //     value: brightness
            //         //     stepSize: plasmoid.configuration.stepSize || 1

            //         //     Timer {
            //         //         id: mouseWheelScrollingDebounceTimer

            //         //         // How long does it take to trigger when the mouse wheel stops scrolling
            //         //         interval: 400

            //         //         // will only be triggered once after restart() called
            //         //         repeat: false
            //         //         running: false
            //         //         triggeredOnStart: false

            //         //         onTriggered: {
            //         //             valuesLock = false
            //         //             executable.exec(plasmoid.configuration.executable + ` set-brightness ${bus_id} ${brightness}`)
            //         //         }
            //         //     }

            //         //     onMoved: () => {
            //         //         // Should also be locked during mouse wheel scrolling.
            //         //         valuesLock = true
            //         //         brightness = value

            //         //         // Handle mouse wheel debounce only when the slider is not pressed.
            //         //         if (!pressed) {
            //         //             mouseWheelScrollingDebounceTimer.restart()
            //         //         }
            //         //     }

            //         //     onPressedChanged: function() {
            //         //         if (pressed) {
            //         //             valuesLock = true
            //         //         } else {
            //         //             // Slider is released
            //         //             valuesLock = false
            //         //             executable.exec(plasmoid.configuration.executable + ` set-brightness ${bus_id} ${brightness}`)
            //         //         }
            //         //     }
            //         // }
            // }

            // Item to fill entire width and the remaining height, this way all other childs of the layout can be centered horizontally
            

            // TextMetrics {
            //     id: percentageMetrics
            //     font: percentageLabel.font
            //     text: '100%'
            // }

        }
    }

    function action_refreshMonitors() {
        monitorDataSource.runOnce();
    }

    Component.onCompleted: function() {
        monitorDataSource.start();
        // code to add new action: Plasmoid.setAction("actionId", i18_n("text"), "iconName") (i18_n without underscore)
        Plasmoid.setAction('refreshMonitors', i18n("Refresh monitors"), 'view-refresh-symbolic');
        // Instead of connecting to a signal of this action, a function called `action_{actionId}` is expected (here action_refreshMonitors)
    }
}
