class BackendInterface {

    constructor(executableDataSource, backendCommand) {
        this.executableDataSource = executableDataSource;
        this.backendCommand = backendCommand;
    }

    set(adapter, id, property, value) {
        const command = `${this.backendCommand} set ${adapter} ${id} ${property} ${value}`;
        this.executableDataSource.exec(command, (exitCode, stdout, stderr) => {
            log(stdout);
        });
    }
    
}
