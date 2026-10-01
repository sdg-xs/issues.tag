param(
    [string]$Case = 'all',
    [string]$TestName = '',
    [string]$KitRoot = 'C:\kit-app-template\_build\windows-x86_64\release\kit',
    [string]$DependencyRoot = '',
    [switch]$Visible
)
$ErrorActionPreference = 'Stop'
$outputPath = Join-Path $PSScriptRoot 'verification'
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null
if (-not $DependencyRoot) { $DependencyRoot = Join-Path (Split-Path $PSScriptRoot -Parent) 'verification-dependencies' }
foreach ($folder in @('extscache', 'extscore', 'exts', 'project-exts')) {
    if (-not (Test-Path -LiteralPath (Join-Path $DependencyRoot $folder) -PathType Container)) {
        throw "Prepare ordinary copies of SDK extscache, extscore, exts and project-exts (section.box) in $DependencyRoot before verification. Shared dependency folders must not be used after the reload incident."
    }
}
$pythonPath = Join-Path $KitRoot 'python\python.exe'
& $pythonPath (Join-Path $PSScriptRoot 'tools\verification_dependencies.py') validate $DependencyRoot --project-root $PSScriptRoot
if ($LASTEXITCODE -ne 0) { throw 'Private dependency snapshot validation failed; Kit was not launched.' }
$privateFolders = @((Join-Path $DependencyRoot 'extscore'), (Join-Path $DependencyRoot 'exts')) | ConvertTo-Json -Compress
$searchFolders = @((Join-Path $DependencyRoot 'extscache'), (Join-Path $DependencyRoot 'project-exts'), (Split-Path $PSScriptRoot -Parent)) | ConvertTo-Json -Compress
$resultsPath = Join-Path $outputPath 'results.json'
if (Test-Path -LiteralPath $resultsPath) { Remove-Item -LiteralPath $resultsPath }
$progressPath = Join-Path $outputPath 'progress.json'
if (Test-Path -LiteralPath $progressPath) { Remove-Item -LiteralPath $progressPath }
foreach ($milestone in @('capture-cycle.json', 'capture-probe.json')) {
    $milestonePath = Join-Path $outputPath $milestone
    if (Test-Path -LiteralPath $milestonePath) { Remove-Item -LiteralPath $milestonePath }
}
$kitArgs = @(
    (Join-Path $PSScriptRoot 'tests\issues_test.kit'),
    '--exec', (Join-Path $PSScriptRoot 'tests\verify_kit.py'),
    "--/exts/issues.tag/verificationCase=$Case",
    "--/exts/issues.tag/verificationTestName=$TestName",
    "--/exts/issues.tag/verificationVisible=$($Visible.IsPresent.ToString().ToLower())",
    "--/exts/issues.tag/verificationDependencyRoot=$DependencyRoot",
    "--/log/file=$outputPath/kit.log",
    "--/app/userConfigPath=$outputPath/user.config.json",
    "--/app/cachePath=$outputPath/cache",
    "--/app/dataPath=$outputPath/data",
    "--/app/exts/foldersCore=$privateFolders",
    "--/app/exts/folders=$searchFolders",
    "--/app/extensions/registryCacheFull=$outputPath/installed-exts",
    "--/exts/omni.kit.registry.nucleus/cachePath=$outputPath/registry-cache",
    '--/exts/omni.kit.registry.nucleus/cacheCreateLinks=false',
    '--/exts/omni.kit.registry.nucleus/cachePrune/enabled=false',
    '--/exts/omni.kit.registry.nucleus/cacheInvalidateOnPull=false',
    '--/app/extensions/registryEnabled=false'
)
if (-not $Visible) { $kitArgs += '--no-window' }
& (Join-Path $KitRoot 'kit.exe') @kitArgs *> (Join-Path $outputPath 'stdout.log')
$processCode = $LASTEXITCODE
if (-not (Test-Path -LiteralPath $resultsPath)) {
    Get-Content (Join-Path $outputPath 'stdout.log') -Tail 25
    if (Test-Path -LiteralPath $progressPath) { Get-Content -LiteralPath $progressPath }
    throw "Kit exited $processCode without a verification report."
}
$report = Get-Content -LiteralPath $resultsPath -Raw | ConvertFrom-Json
$report.results | ForEach-Object { Write-Output ($_.state + ': ' + $_.name); if ($_.error) { Write-Output $_.error } }
Write-Output ("Passed " + $report.passed + ', failed ' + $report.failed)
if ($processCode -ne 0 -or $report.failed -ne 0) { exit 1 }
exit 0
