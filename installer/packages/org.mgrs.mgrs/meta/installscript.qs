function Component() {
    // Default constructor
}

Component.prototype.createOperations = function() {
    // Call default implementation to install files and create shortcuts
    component.createOperations();

    if (systemInfo.productType === "windows") {
        // Create a desktop shortcut
        component.addOperation("CreateShortcut",
            "@TargetDir@/mgrs_gui.py",
            "@DesktopDir@/MGR-S.lnk",
            "workingDirectory=@TargetDir@",
            "iconPath=%SystemRoot%/system32/python3.exe");
    }
};

Component.prototype.validateInstallation = function() {
    var result = QInstaller.PackageManagerCore.installationSuccess;
    if (systemInfo.productType === "windows" && systemInfo.productVersion < "10.0.18362") {
        result = QInstaller.PackageManagerCore.installationFailed;
        installer.setValue("Installer.InstallationErrors", "MGR-S requires Windows 10 version 1903 or later");
    }
    return result;
};
