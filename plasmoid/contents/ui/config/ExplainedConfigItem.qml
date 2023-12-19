import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15 as QQC2

import org.kde.plasma.core 2.0 as PlasmaCore
import org.kde.kirigami 2.4 as Kirigami

ColumnLayout {
    enum Type {
        Int,
        Double,
        String,
        Bool
    }

    property var input_int_validator: IntValidator{bottom: 0}
    property var input_double_validator: DoubleValidator{bottom: 0}
    property var input_string_validator: RegExpValidator{}

    required property string name
    required property string description
    required property int type
    required property var default_value
    property string unit
    
    // bidirectional bindings cannot be conditional
    property alias value: textInput.text
    property alias checked: toggle.checked

    RowLayout {
        QQC2.CheckBox {
            id: toggle
            text: name
        }
        QQC2.TextField {
            id: textInput
            validator: {
                if (type == ExplainedConfigItem.Type.Int) {
                    return input_int_validator;
                } else if (type == ExplainedConfigItem.Type.Double) {
                    return input_double_validator;
                } else {
                    return input_string_validator;
                }
            }
            visible: type != ExplainedConfigItem.Type.Bool
            enabled: toggle.checked
        }
        QQC2.Label {
            visible: unit
            color: toggle.checked ? PlasmaCore.Theme.textColor : PlasmaCore.Theme.disabledTextColor
            text: unit
        }
    }

    QQC2.Label {
        text: description
        onLinkActivated: link => Qt.openUrlExternally(link);
        visible: description
        leftPadding: 2 * PlasmaCore.Units.largeSpacing
        font: PlasmaCore.Theme.smallestFont
    }
}
