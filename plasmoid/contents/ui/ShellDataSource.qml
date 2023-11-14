import org.kde.plasma.core 2.0 as PlasmaCore

import "code/util.js" as Util

PlasmaCore.DataSource {
    engine: "executable"
    connectedSources: []
    function exec(command, callback) {
        Util.log(`Execute command: ${command}`);
        const wrappedCallback = (calledCommand, data) => {
            if (calledCommand === command) {
                const exitCode = data["exit code"];
                const stdout = data.stdout;
                const stderr = data.stderr;
                Util.log(`[code]  : ${command}: ${exitCode}`);
                Util.log(`[stdout]: ${command}: ${Util.removeTrailingNewlines(stdout)}`);
                Util.log(`[stderr]: ${command}: ${Util.removeTrailingNewlines(stderr)}\n`);
                if (callback) {
                    callback(exitCode, stdout, stderr);
                }
                disconnectSource(command);
                onNewData.disconnect(wrappedCallback);
            }
        };
        onNewData.connect(wrappedCallback);
        connectSource(command);
    }
}
