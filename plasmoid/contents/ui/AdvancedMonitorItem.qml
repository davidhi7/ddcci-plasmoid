import QtQuick 2.15
import QtQuick.Layouts 1.15

import org.kde.plasma.plasmoid 2.0
import org.kde.plasma.core 2.1 as PlasmaCore
import org.kde.plasma.components 3.0 as PlasmaComponents
import org.kde.plasma.extras 2.0 as PlasmaExtras

PlasmaComponents.ItemDelegate {
    id: root
    // Do not show background with accent colour
    background.visible: false

    required property var model

    contentItem: ColumnLayout {
        RowLayout {
            
            PlasmaExtras.Heading {
                level: 4
                text: model.name

                // TODO is this right?
                Layout.fillWidth: true
            }

            PlasmaComponents.ComboBox {
                model: ["1", "2", "3", "4", "5"]
                Layout.alignment: Qt.AlignRight
            }
        }

        HorizontalLine {
            color: PlasmaCore.Theme.highlightColor
        }

        ContinuousFeatureSlider {
            propertyName: i18n("brightness:")
            propertyStepSize: plasmoid.configuration.stepSize
            value: model.property_values['brightness']['value']
        }

        ContinuousFeatureSlider {
            propertyName: i18n("contrast:")
            propertyStepSize: plasmoid.configuration.stepSize
            value: model.property_values['contrast']['value']
        }
    }
}
