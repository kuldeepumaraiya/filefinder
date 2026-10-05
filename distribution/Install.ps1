$ErrorActionPreference = 'Stop'
$installSource = $PSScriptRoot
$installTarget = Join-Path $env:LOCALAPPDATA 'Programs\FileFinder'
if (Get-Process -Name FileFinder -ErrorAction SilentlyContinue) {
    throw 'Close FileFinder before installing or updating it, then run Install.cmd again.'
}
if (-not (Test-Path -LiteralPath (Join-Path $installSource 'FileFinder.exe')) -or -not (Test-Path -LiteralPath (Join-Path $installSource '_internal'))) {
    throw 'Extract the entire ZIP first. FileFinder.exe and _internal must be next to this installer.'
}
if ([IO.Path]::GetFullPath($installSource).TrimEnd('\') -eq [IO.Path]::GetFullPath($installTarget).TrimEnd('\')) {
    throw 'This app is already in its installation folder. Open FileFinder.exe directly.'
}
New-Item -ItemType Directory -Path $installTarget -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $installSource 'FileFinder.exe') -Destination $installTarget -Force
Copy-Item -LiteralPath (Join-Path $installSource '_internal') -Destination $installTarget -Recurse -Force
foreach ($installFile in @('LICENSE','README.txt','THIRD_PARTY_NOTICES.md')) {
    Copy-Item -LiteralPath (Join-Path $installSource $installFile) -Destination $installTarget -Force
}
Copy-Item -LiteralPath (Join-Path $installSource 'licenses') -Destination $installTarget -Recurse -Force
$shortcutShell = New-Object -ComObject WScript.Shell
$programsFolder = [Environment]::GetFolderPath('Programs')
$desktopFolder = [Environment]::GetFolderPath('Desktop')
foreach ($shortcutFolder in @($programsFolder,$desktopFolder)) {
    $appShortcut = $shortcutShell.CreateShortcut((Join-Path $shortcutFolder 'FileFinder.lnk'))
    $appShortcut.TargetPath = Join-Path $installTarget 'FileFinder.exe'
    $appShortcut.WorkingDirectory = $installTarget
    $appShortcut.IconLocation = (Join-Path $installTarget 'FileFinder.exe') + ',0'
    $appShortcut.Description = 'Find files by name or document text'
    $appShortcut.Save()
}
Write-Host "Installed FileFinder to $installTarget"
Write-Host 'Open FileFinder from your desktop or Start Menu. Pin its running icon to the taskbar.'
Start-Process -FilePath (Join-Path $installTarget 'FileFinder.exe') -WindowStyle Hidden
