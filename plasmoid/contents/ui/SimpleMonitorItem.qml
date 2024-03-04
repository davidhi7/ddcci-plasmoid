import QtQuick
import QtQuick.Layouts

import org.kde.plasma.plasmoid
import org.kde.plasma.components as PlasmaComponents

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
