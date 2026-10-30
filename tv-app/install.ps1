# Packages a TV app folder and installs it on a Samsung TV in Developer Mode.
# Usage (PowerShell, from this folder):
#   .\install.ps1 -TvIp 192.168.1.50 -CertProfile TVHome            # home screen
#   .\install.ps1 -TvIp 192.168.1.50 -CertProfile TVHome -App Nama  # 30nama shortcut
param(
    [Parameter(Mandatory = $true)][string]$TvIp,
    [string]$CertProfile = "TVHome",
    [string]$App = "TVHome",
    [string]$TizenRoot = "C:\tizen-studio"
)
$ErrorActionPreference = "Stop"

$tizen = Join-Path $TizenRoot "tools\ide\bin\tizen.bat"
$sdb   = Join-Path $TizenRoot "tools\sdb.exe"
$dir   = Join-Path $PSScriptRoot $App
$serial = "${TvIp}:26101"

foreach ($f in @($tizen, $sdb, $dir)) {
    if (-not (Test-Path $f)) { throw "Not found: $f" }
}

Write-Host "1/3 Connecting to TV at $serial ..."
& $sdb connect $TvIp
& $sdb devices

Write-Host "2/3 Packaging and signing $App with profile '$CertProfile' ..."
Get-ChildItem $dir -Filter *.wgt | Remove-Item
& $tizen package -t wgt -s $CertProfile -- $dir
$wgt = Get-ChildItem $dir -Filter *.wgt | Select-Object -First 1
if (-not $wgt) { throw "Packaging failed - no .wgt was created. Check the certificate profile name." }

Write-Host "3/3 Installing $($wgt.Name) on the TV ..."
& $tizen install -n $wgt.Name -s $serial -- $dir

Write-Host "Done. Look for the app in the TV's Apps list."
