param(
    [string]$Case = 'all',
    [string]$TestName = '',
    [string]$KitRoot = 'C:\kit-app-template\_build\windows-x86_64\release\kit',
    [switch]$Visible
)
$ErrorActionPreference = 'Stop'
$outputPath = Join-Path $PSScriptRoot 'verification'
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
$resultsPath = Join-Path $outputPath 'results.json'
if (Test-Path -LiteralPath $resultsPath) { Remove-Item -LiteralPath $resultsPath }
$kitArgs = @(
    (Join-Path $PSScriptRoot 'tests\issues_test.kit'),
    '--ext-folder', (Join-Path (Split-Path $KitRoot -Parent) 'extscache'),
    '--ext-folder', (Split-Path $PSScriptRoot -Parent),
    '--exec', (Join-Path $PSScriptRoot 'tests\verify_kit.py'),
    "--/exts/issues.tag/verificationCase=$Case",
    "--/exts/issues.tag/verificationTestName=$TestName",
    "--/exts/issues.tag/verificationVisible=$($Visible.IsPresent.ToString().ToLower())",
    "--/log/file=$outputPath/kit.log",
    "--/app/userConfigPath=$outputPath/user.config.json",
    "--/app/cachePath=$outputPath/cache",
    "--/app/dataPath=$outputPath/data"
)
if (-not $Visible) { $kitArgs += '--no-window' }
& (Join-Path $KitRoot 'kit.exe') @kitArgs *> (Join-Path $outputPath 'stdout.log')
$processCode = $LASTEXITCODE
if (-not (Test-Path -LiteralPath $resultsPath)) {
    Get-Content (Join-Path $outputPath 'stdout.log') -Tail 25
    throw "Kit exited $processCode without a verification report."
}
$report = Get-Content -LiteralPath $resultsPath -Raw | ConvertFrom-Json
$report.results | ForEach-Object { Write-Output ($_.state + ': ' + $_.name); if ($_.error) { Write-Output $_.error } }
Write-Output ("Passed " + $report.passed + ', failed ' + $report.failed)
if ($processCode -ne 0 -or $report.failed -ne 0) { exit 1 }
exit 0
