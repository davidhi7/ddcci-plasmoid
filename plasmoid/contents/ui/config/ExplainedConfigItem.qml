import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15 as QQC2

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
    property string unit
    
    // bidirectional bindings cannot be conditional (?)
    property alias value: textInput.text
    property alias checked: boolInput.checked

    Kirigami.FormData.label: name
    Kirigami.FormData.labelAlignment: Qt.AlignTop

    RowLayout {
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
        }
        QQC2.CheckBox {
            id: boolInput
            visible: type == ExplainedConfigItem.Type.Bool
        }
        QQC2.Label {
            text: unit
            visible: unit
        }
    }
    QQC2.Label {
        text: description
        onLinkActivated: link => Qt.openUrlExternally(link);
        visible: description
    }
}
