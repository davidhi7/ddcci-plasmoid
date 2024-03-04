import QtQuick
import org.kde.plasma.configuration

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
