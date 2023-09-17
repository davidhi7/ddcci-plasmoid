import QtQuick 2.15
import QtQuick.Layouts 1.15

import org.kde.plasma.plasmoid 2.0
import org.kde.plasma.core 2.1 as PlasmaCore
import org.kde.plasma.components 3.0 as PlasmaComponents

PlasmaComponents.ItemDelegate {
    required property var model
    required property var backendWrapper

    // Do not show background with accent colour
    background.visible: false
    // Layout.fillWidth: true
    Layout.alignment: Qt.AlignRight

    contentItem: ContinuousFeatureSlider {
        id: slider

        propertyName: model.name
        propertyStepSize: plasmoid.configuration.stepSize
        value: model.property_values['brightness']['value']
        onLocked: () => {
            // TODO impl
        }
        onReleased: (value) => {
            backendWrapper.set(model.adapter, model.id, 'brightness', value);
        }
    }
}
