import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC

import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

// Import ../ShellDataSource.qml
import ".."

KCM.SimpleKCM {
    property alias cfg_ddcci_ddcutil_executable: ddcci_ddcutil_executable.value
    property alias cfg_ddcci_ddcutil_executable_enabled: ddcci_ddcutil_executable.checked
    property alias cfg_ddcci_ddcutil_sleep_multiplier: ddcci_ddcutil_sleep_multiplier.value
    property alias cfg_ddcci_ddcutil_sleep_multiplier_enabled: ddcci_ddcutil_sleep_multiplier.checked
    property alias cfg_ddcci_ddcutil_no_verify: ddcci_ddcutil_no_verify.checked
    property alias cfg_ddcci_brute_force_attempts: ddcci_brute_force_attempts.value
    property alias cfg_ddcci_brute_force_attempts_enabled: ddcci_brute_force_attempts.checked

    ColumnLayout {

        ShellDataSource {
            id: executable
        }

        Kirigami.InlineMessage {
            id: ddcutil_invokation_fail_message
            Layout.fillWidth: true
            text: i18n(
                "Failed to invoke ddcutil. Please consult the <a href=%1>documentation</a> or file a <a href=%2>GitHub issue</a>.",
                "\"https://github.com/davidhi7/ddcci-plasmoid/blob/main/README.md\"", "\"https://github.com/davidhi7/ddcci-plasmoid/issues\""
            )
            onLinkActivated: link => Qt.openUrlExternally(link);
            type: Kirigami.MessageType.Error
            visible: false
            showCloseButton: true
        }

        Kirigami.InlineMessage {
            id: ddcutil_invokation_success_message
            Layout.fillWidth: true
            text: i18n("ddcutil is set up correctly.")
            type: Kirigami.MessageType.Positive
            visible: false
            showCloseButton: true
        }

        QQC.Label {
            text: i18n("External monitors are controlled with <a href=%1>ddcutil</a> over DDC/CI.", "\"https://github.com/rockowitz/ddcutil\"")
            onLinkActivated: link => Qt.openUrlExternally(link);
            Layout.alignment: Qt.AlignHCenter
        }

        Kirigami.FormLayout {
            Kirigami.Separator {
                Kirigami.FormData.label: i18n("ddcutil tweaks")
                Kirigami.FormData.isSection: true
            }

            ExplainedConfigItem {
                id: ddcci_ddcutil_executable
                name: i18n("Overwrite ddcutil executable:")
                type: ExplainedConfigItem.Type.String
                default_value: plasmoid.configuration.ddcci_ddcutil_executableDefault
                description: ""
            }

            ExplainedConfigItem {
                id: ddcci_ddcutil_sleep_multiplier
                name: i18n("Set custom ddcutil sleep time multiplier:")
                description: i18n("Assign a custom value to the ddcutil --sleep-multiplier option.<br>See the <a href=%1>corresponding ddcutil docs</a>.", "\"https://www.ddcutil.com/performance_options/#option-sleep-multiplier\"")
                type: ExplainedConfigItem.Type.Double
                default_value: plasmoid.configuration.ddcci_ddcutil_sleep_multiplierDefault
            }

            ExplainedConfigItem {
                id: ddcci_ddcutil_no_verify
                name: i18n("Enable ddcutil noverify option")
                description: i18n("Enable the --noverify option of ddcutil.<br>See the <a href=%1>corresponding ddcutil docs</a>.", "\"https://www.ddcutil.com/command_setvcp/#option-noverify\"")
                type: ExplainedConfigItem.Type.Bool
                default_value: plasmoid.configuration.ddcci_ddcutil_no_verifyDefault
            }

            ExplainedConfigItem {
                id: ddcci_brute_force_attempts
                name: i18n("Retry ddcutil commands:")
                description: i18n("Repeat ddcutil commands so many times if they fail.")
                type: ExplainedConfigItem.Type.Int
                unit: i18nc("Something is repeated so many times", "times")
                default_value: ddcci_brute_force_attempts.ddcci_brute_force_attemptsDefault
            }
        }

        QQC.Button {
            id: ddcutil_invokation_button
            text: i18n("Verify ddcutil installation")
            Layout.topMargin: Kirigami.Units.smallSpacing
            onClicked: {
                ddcutil_invokation_button.enabled = false;
                ddcutil_invokation_success_message.visible = false;
                ddcutil_invokation_fail_message.visible = false;
                executable.exec(`"${cfg_ddcci_ddcutil_executable}" detect`, (exitCode, stdout, stderr) => {
                    ddcutil_invokation_button.enabled = true;
                    if (exitCode == 0) {
                        ddcutil_invokation_success_message.visible = true;
                    } else {
                        ddcutil_invokation_fail_message.visible = true;
                    }
                });
            }
            Layout.alignment: Qt.AlignHCenter
        }

        Item {
            Layout.fillHeight: true
        }
    }
}
