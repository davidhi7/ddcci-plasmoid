import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15 as QQC2

import org.kde.plasma.core 2.0 as PlasmaCore
import org.kde.kirigami 2.4 as Kirigami

// Import ../ShellDataSource.qml
import ".."

ColumnLayout {
    property alias cfg_ddcci_ddcutil_executable: ddcci_ddcutil_executable.value
    property alias cfg_ddcci_ddcutil_sleep_multiplier: ddcutil_sleep_multiplier.value
    property alias cfg_ddcci_ddcutil_no_verify: ddcci_ddcutil_no_verify.checked
    property alias cfg_ddcci_brute_force_attempts: ddcci_brute_force_attempts.value

    ShellDataSource {
        id: executable
    }

    Kirigami.InlineMessage {
        id: ddcutil_invokation_fail_message
        Layout.fillWidth: true
        text: "Failed to invoke ddcutil. Please consult the <a href=\"https://github.com/davidhi7/ddcci-plasmoid/blob/main/README.md\">documentation</a> or file a <a href=\"https://github.com/davidhi7/ddcci-plasmoid/issues\">GitHub issue</a>."
        onLinkActivated: link => Qt.openUrlExternally(link);
        type: Kirigami.MessageType.Error
        visible: false
        showCloseButton: true
    }

    Kirigami.InlineMessage {
        id: ddcutil_invokation_success_message
        Layout.fillWidth: true
        text: "ddcutil is set up correctly."
        type: Kirigami.MessageType.Positive
        visible: false
        showCloseButton: true
    }

    QQC2.Label {
        text: i18n("External monitors are controlled with <a href=\"https://github.com/rockowitz/ddcutil\">ddcutil</a> over DDC/CI.")
        onLinkActivated: link => Qt.openUrlExternally(link);
        Layout.alignment: Qt.AlignHCenter
    }

    Kirigami.FormLayout {
        ExplainedConfigItem {
            id: ddcci_ddcutil_executable
            name: i18n("ddcutil executable:")
            type: ExplainedConfigItem.Type.String
        }

        QQC2.Button {
            id: ddcutil_invokation_button
            text: i18n("Verify ddcutil installation")
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

        ExplainedConfigItem {
            id: ddcutil_sleep_multiplier
            name: i18n("ddcutil sleep_mutliplier:")
            description: i18n("Assign a custom value to the ddcutil --sleep-multiplier flag.<br>See the <a href=\"https://www.ddcutil.com/performance_options/#option-sleep-multiplier\">corresponding ddcutil docs</a>.")
            type: ExplainedConfigItem.Type.Double
        }

        ExplainedConfigItem {
            id: ddcci_ddcutil_no_verify
            name: i18n("ddcutil noverify:")
            description: i18n("Enable the ddcutil --noverify flag.<br>See the <a href=\"https://www.ddcutil.com/command_setvcp/#option-noverify\">corresponding ddcutil docs</a>.")
            type: ExplainedConfigItem.Type.Bool
        }

        ExplainedConfigItem {
            id: ddcci_brute_force_attempts
            name: i18n("Retry ddcutil commands:")
            description: i18n("Repeat ddcutil commands up to N times if they fail.")
            type: ExplainedConfigItem.Type.Int
            unit: i18n("times")
        }
    }

    Item {
        Layout.fillHeight: true
    }
}
