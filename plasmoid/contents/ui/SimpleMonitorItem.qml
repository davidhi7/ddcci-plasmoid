import QtQuick 2.15
import QtQuick.Layouts 1.15

import org.kde.plasma.plasmoid 2.0
import org.kde.plasma.core 2.1 as PlasmaCore
import org.kde.plasma.components 3.0 as PlasmaComponents

ContinuousFeatureSlider {
    required property var model

    propertyName: model.name
    propertyStepSize: plasmoid.configuration.stepSize
    value: model.property_values['brightness']['value']
}
// PlasmaComponents.ItemDelegate {
//     id: root
//     // Do not show background with accent colour
//     background.visible: false

//     required property var model

//     contentItem: ContinuousFeatureSlider {
//         propertyName: model.name
//         stepSize: plasmoid.configuration.stepSize
//         value: model.property_values['brightness']['value']
//     }
// }
