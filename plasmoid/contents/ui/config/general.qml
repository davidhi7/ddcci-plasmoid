import QtQuick 2.0
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15 as QQC2
import QtQuick.Dialogs 1.3 as QQD2

import org.kde.kirigami 2.4 as Kirigami

Kirigami.FormLayout {
    id: page

    property alias cfg_stepSize: stepSize.text
    property alias cfg_executable: executable.text
    property alias cfg_enableAdvancedMode: enableAdvancedMode.checked

    property alias cfg_ddcciMonitorsEnabled: ddcciMonitorsEnabled.checked
    property alias cfg_builtinMonitorsEnabled: builtinMonitorsEnabled.checked

    property alias cfg_general_enable_logging: general_enable_logging.checked
    property string cfg_general_log_file

    QQC2.TextField {
        id: stepSize
        Kirigami.FormData.label: i18n("Step size:")
        validator: RegExpValidator{regExp: /^[0-9,/]+$/}
    }

    QQC2.TextField {
        id: executable
        Kirigami.FormData.label: i18n("Backend executable command:")
    }

    QQC2.CheckBox {
        id: enableAdvancedMode
        Kirigami.FormData.label: i18n("Show contrast sliders and power button:")
    }

    QQC2.CheckBox {
        id: ddcciMonitorsEnabled
        Kirigami.FormData.label: i18n("External monitors with DDC/CI support:")
    }
    
    QQC2.CheckBox {
        id: builtinMonitorsEnabled
        Kirigami.FormData.label: i18n("Builtin laptop monitors:")
    }
    
    Kirigami.Separator {
        Kirigami.FormData.label: i18n("Debugging options")
        Kirigami.FormData.isSection: true
    }

    QQC2.CheckBox {
        id: general_enable_logging
        Kirigami.FormData.label: i18n("Enable logging:")
    }

    RowLayout {
        Kirigami.FormData.label: i18n("Log file:")

        QQC2.Button {
            text: cfg_general_log_file ? cfg_general_log_file : i18n("Choose log file")
            onClicked: log_file_dialog.open()
        }

        QQC2.Button {
            icon.name: "edit-clear-symbolic"
            enabled: cfg_general_log_file
            onClicked: cfg_general_log_file = ""
        }

        QQD2.FileDialog {
            id: log_file_dialog
            title: i18n("Choose log file")
            folder: shortcuts.home
            defaultSuffix: "log"
            selectMultiple: false
            selectExisting: false
            onAccepted: {
                if (fileUrl.toString().startsWith("file://")) {
                    cfg_general_log_file = fileUrl.toString().substring(7);
                }
            }
        }
    }
}
