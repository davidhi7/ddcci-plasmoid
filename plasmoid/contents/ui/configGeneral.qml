import QtQuick 2.0
import QtQuick.Controls 2.5 as QQC2
import org.kde.kirigami 2.4 as Kirigami

Kirigami.FormLayout {
    id: page

    property alias cfg_stepSize: stepSize.text

    QQC2.TextField {
        id: stepSize
        Kirigami.FormData.label: 'Step size:'
        validator: RegExpValidator{regExp: /^[0-9,/]+$/}
    }
}