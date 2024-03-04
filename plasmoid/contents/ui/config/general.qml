import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC
import QtQuick.Dialogs as QQD

import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    property alias cfg_stepSize: stepSize.text
    property alias cfg_executable: executable.text
    property alias cfg_enableAdvancedMode: enableAdvancedMode.checked

    property alias cfg_ddcciMonitorsEnabled: ddcciMonitorsEnabled.checked
    property alias cfg_builtinMonitorsEnabled: builtinMonitorsEnabled.checked

    property alias cfg_general_enable_logging: general_enable_logging.checked
    property string cfg_general_log_file

    Kirigami.FormLayout {
        QQC.TextField {
            id: stepSize
            Kirigami.FormData.label: i18n("Step size:")
            validator: RegularExpressionValidator{regularExpression: /^[0-9,/]+$/}
        }

        QQC.TextField {
            id: executable
            Kirigami.FormData.label: i18n("Backend executable command:")
        }

        QQC.CheckBox {
            id: enableAdvancedMode
            Kirigami.FormData.label: i18n("Show contrast sliders and power button:")
        }

        QQC.CheckBox {
            id: ddcciMonitorsEnabled
            Kirigami.FormData.label: i18n("External monitors with DDC/CI support:")
        }
        
        QQC.CheckBox {
            id: builtinMonitorsEnabled
            Kirigami.FormData.label: i18n("Builtin laptop monitors:")
        }
        
        Kirigami.Separator {
            Kirigami.FormData.label: i18n("Debugging options")
            Kirigami.FormData.isSection: true
        }

        QQC.CheckBox {
            id: general_enable_logging
            Kirigami.FormData.label: i18n("Enable logging:")
        }

        RowLayout {
            Kirigami.FormData.label: i18n("Log file:")

            QQC.Button {
                text: cfg_general_log_file ? cfg_general_log_file : i18n("Choose log file")
                onClicked: log_file_dialog.open()
            }

            QQC.Button {
                icon.name: "edit-clear-symbolic"
                enabled: cfg_general_log_file
                onClicked: cfg_general_log_file = ""
            }

            QQD.FileDialog {
                id: log_file_dialog
                title: i18n("Choose log file")
                currentFolder: shortcuts.home
                defaultSuffix: "log"
                fileMode: QQD.FileDialog.SaveFile
                onAccepted: {
                    if (fileUrl.toString().startsWith("file://")) {
                        cfg_general_log_file = fileUrl.toString().substring(7);
                    }
                }
            }
        }
    }
}
