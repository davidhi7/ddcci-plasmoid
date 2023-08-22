import QtQuick 2.15
import QtQuick.Layouts 1.15

import org.kde.plasma.plasmoid 2.0
import org.kde.plasma.components 3.0 as PlasmaComponents
import org.kde.plasma.core 2.1 as PlasmaCore

RowLayout {
    required property string propertyName
    required property int propertyStepSize

    property alias value: slider.value
    property alias intValue: slider.intValue

    Layout.alignment: Qt.AlignRight
    spacing: PlasmaCore.Units.gridUnit
    
    PlasmaComponents.Label {
        text: propertyName

        // TODO test layout stuff
        // Layout.fillWidth: true
        horizontalAlignment: Qt.AlignLeft
    }

    PlasmaComponents.Slider {
        id: slider

        // TODO test layout stuff
        Layout.fillWidth: !outsideSysTray
        from: 0
        to: 100
        stepSize: Math.max(propertyStepSize, 1)

        property int intValue: Math.round(value)

        Timer {
            id: mouseWheelScrollingDebounceTimer

            // Time between latest mouse wheel interaction and call of the backend
            interval: 400

            // will only be triggered once after restart() called
            repeat: false
            running: false
            triggeredOnStart: false

            onTriggered: {
                valuesLock = false;
                // TODO set command stuff
                console.log(`value updated to ${slider.value}`);
            }
        }

        onMoved: {
            // Should also be locked during mouse wheel scrolling.
            valuesLock = true;
            // TODO ?
            // brightness = value;

            // Handle mouse wheel debounce only when the slider is not pressed.
            if (!pressed) {
                mouseWheelScrollingDebounceTimer.restart();
            }
        }

        onPressedChanged: function() {
            if (pressed) {
                valuesLock = true;
            } else {
                // Slider is released
                valuesLock = false;
                // TODO set command stuff
                console.log(`value updated to ${slider.value}`);
            }
        }
    }

    PlasmaComponents.Label {
        horizontalAlignment: Qt.AlignRight
        Layout.minimumWidth: percentageMetrics.advanceWidth
        text: slider.intValue + '%'

        TextMetrics {
            id: percentageMetrics
            text: '100%'
        }
    }
}
