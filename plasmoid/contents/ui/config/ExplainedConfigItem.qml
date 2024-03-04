import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC

import org.kde.kirigami as Kirigami

ColumnLayout {
    enum Type {
        Int,
        Double,
        String,
        Bool
    }

    property var input_int_validator: IntValidator{bottom: 0}
    property var input_double_validator: DoubleValidator{bottom: 0}
    property var input_string_validator: RegularExpressionValidator{}

    required property string name
    required property string description
    required property int type
    required property var default_value
    property string unit
    
    // bidirectional bindings cannot be conditional
    property alias value: textInput.text
    property alias checked: toggle.checked

    RowLayout {
        QQC.CheckBox {
            id: toggle
            text: name
        }
        QQC.TextField {
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
        QQC.Label {
            visible: unit
            color: toggle.checked ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
            text: unit
        }
    }

    QQC.Label {
        text: description
        onLinkActivated: link => Qt.openUrlExternally(link);
        visible: description
        leftPadding: 2 * Kirigami.Units.largeSpacing
        font: Kirigami.Theme.smallestFont
    }
}
