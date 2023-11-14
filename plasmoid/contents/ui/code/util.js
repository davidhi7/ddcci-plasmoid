.import org.kde.plasma.plasmoid 2.0 as PlasmoidenableLogging

function log(message) {
    if (plasmoid.configuration.enableLogging) {
        console.log(`LOGGING: ${message}`);
    }
}

function removeTrailingNewlines(arg) {
    return arg.replace(/\n$/, '');
}
