import QtQuick
import QtQuick.Layouts

import org.kde.plasma.plasmoid
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.extras as PlasmaExtras

import org.kde.kirigami as Kirigami

PlasmaComponents.ItemDelegate {
    required property var model
    required property var backendWrapper

    // Do not show background with accent colour
    background.visible: false

    contentItem: ColumnLayout {
        RowLayout {
            
            PlasmaExtras.Heading {
                level: 4
                text: model.name

                Layout.fillWidth: true
            }

            PlasmaComponents.ToolButton {
                icon.name: 'system-shutdown-symbolic'
                Layout.alignment: Qt.AlignRight
                // TODO handler
            }
        }

        ContinuousFeatureSlider {
            propertyName: i18n("brightness:")
            propertyStepSize: plasmoid.configuration.stepSize
            value: model.property_values['brightness']['value']
            onLocked: () => {
                // TODO impl
            }
            onReleased: (value) => {
                backendWrapper.set(model.adapter, model.id, 'brightness', value);
            }
        }

        ContinuousFeatureSlider {
            propertyName: i18n("contrast:")
            propertyStepSize: plasmoid.configuration.stepSize
            value: model.property_values['contrast']['value']
            onLocked: () => {
                // TODO impl
            }
            onReleased: (value) => {
                backendWrapper.set(model.adapter, model.id, 'contrast', value);
            }
        }
    }
}
