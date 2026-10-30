# Packages the TVHome app and installs it on a Samsung TV in Developer Mode.
# Usage (PowerShell, from this folder):
#   .\install.ps1 -TvIp 192.168.1.50 -CertProfile TVHome
param(
    [Parameter(Mandatory = $true)][string]$TvIp,
    [string]$CertProfile = "TVHome",
    [string]$TizenRoot = "C:\tizen-studio"
)
$ErrorActionPreference = "Stop"

$tizen = Join-Path $TizenRoot "tools\ide\bin\tizen.bat"
$sdb   = Join-Path $TizenRoot "tools\sdb.exe"
$app   = Join-Path $PSScriptRoot "TVHome"
$wgt   = Join-Path $app "Home.wgt"
$serial = "${TvIp}:26101"

foreach ($f in @($tizen, $sdb)) {
    if (-not (Test-Path $f)) { throw "Not found: $f  (is Tizen Studio installed in $TizenRoot?)" }
}

Write-Host "1/3 Connecting to TV at $serial ..."
& $sdb connect $TvIp
& $sdb devices

Write-Host "2/3 Packaging and signing with profile '$CertProfile' ..."
if (Test-Path $wgt) { Remove-Item $wgt }
& $tizen package -t wgt -s $CertProfile -- $app
if (-not (Test-Path $wgt)) { throw "Packaging failed - Home.wgt was not created. Check the certificate profile name." }

Write-Host "3/3 Installing on the TV ..."
& $tizen install -n Home.wgt -s $serial -- $app

Write-Host "Done. Look for 'Home' in the TV's Apps list."
