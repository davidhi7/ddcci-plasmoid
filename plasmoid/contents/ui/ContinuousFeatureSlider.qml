import QtQuick 2.15
import QtQuick.Layouts 1.15

import org.kde.plasma.plasmoid 2.0
import org.kde.plasma.components 3.0 as PlasmaComponents
import org.kde.plasma.core 2.1 as PlasmaCore

RowLayout {
    required property string propertyName
    required property int propertyStepSize

    property alias value: slider.value

    Layout.alignment: Qt.AlignRight
    spacing: PlasmaCore.Units.gridUnit

    signal locked()
    signal released(int value)
    
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

        Timer {
            id: mouseWheelScrollingDebounceTimer

            // Time between latest mouse wheel interaction and call of the backend
            interval: 400

            // will only be triggered once after restart() called
            repeat: false
            running: false
            triggeredOnStart: false

            onTriggered: {
                released(slider.value);
            }
        }

        onMoved: {
            // Lock if the slider was moved by mouse buttons or scrolling
            locked();

            // Handle mouse wheel debounce only when the slider is not pressed but moved by scrolling
            if (!pressed) {
                mouseWheelScrollingDebounceTimer.restart();
            }
        }

        onPressedChanged: function() {
            if (pressed) {
                // Slider is pressed
                locked();
            } else {
                // Slider is released
                released(slider.value);
            }
        }
    }

    PlasmaComponents.Label {
        horizontalAlignment: Qt.AlignRight
        Layout.minimumWidth: percentageMetrics.advanceWidth
        text: slider.value + '%'

        TextMetrics {
            id: percentageMetrics
            text: '100%'
        }
    }
}
