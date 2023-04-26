import QtQuick 2.15
import QtQuick.Layouts 1.15

import QtQuick.Controls 2.5 as QQC2
import org.kde.kirigami 2.4 as Kirigami

Kirigami.FormLayout {
    id: page

    property alias cfg_stepSize: stepSize.text
    property alias cfg_executable: executable.text
    property alias cfg_ddcutilSkipVerification: ddcutilSkipVerification.checked

    QQC2.TextField {
        id: stepSize
        Kirigami.FormData.label: i18n("Step size:")
        validator: RegExpValidator{regExp: /^[0-9,/]+$/}
    }

    QQC2.TextField {
        id: executable
        Kirigami.FormData.label: i18n("Backend executable command:")
    }

    Kirigami.Separator {
        Kirigami.FormData.isSection: true
        Kirigami.FormData.label: i18n("ddcutil specific options")
    }

    ColumnLayout {
        Kirigami.FormData.label: i18n("Skip verification after setvcp:")
        Kirigami.FormData.labelAlignment: Qt.AlignTop
        QQC2.CheckBox {
            id: ddcutilSkipVerification
        }
        QQC2.Label {
            text: "Disabling verification can fix errors for some monitors.<br>See the <a href=\"https://www.ddcutil.com/command_setvcp/#option-noverify\">ddcutil docs</a>."
            // text: "See the docs.\nDisabling verification can fix errors for some monitors."
            onLinkActivated: link => Qt.openUrlExternally(link)
            // elide: Text.elideLeft
        }
    }
}
