import QtQuick 2.0
import org.kde.plasma.configuration 2.0

ConfigModel {
    ConfigCategory {
        name: i18n("General")
        icon: 'configure'
        source: 'config/general.qml'
    }
    ConfigCategory {
        name: i18n("External monitors")
        icon: 'monitor'
        source: 'config/ddcci.qml'
    }
}
