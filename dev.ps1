param(
    [string]$BackendHost = '127.0.0.1',
    [int]$BackendPort = 8000
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$python = if (Test-Path (Join-Path $root '.venv\Scripts\python.exe')) {
    Join-Path $root '.venv\Scripts\python.exe'
} else {
    'python'
}
$logDirectory = Join-Path $root '.tmp'
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
$stdoutLog = Join-Path $logDirectory 'django-dev.stdout.log'
$stderrLog = Join-Path $logDirectory 'django-dev.stderr.log'
$backend = $null

try {
    Write-Host "Starting Django at http://${BackendHost}:${BackendPort} ..." -ForegroundColor Cyan
    $backend = Start-Process -FilePath $python `
        -ArgumentList 'manage.py', 'runserver', "${BackendHost}:${BackendPort}", '--noreload' `
        -WorkingDirectory $root -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog

    $ready = $false
    for ($attempt = 1; $attempt -le 60; $attempt++) {
        Start-Sleep -Seconds 1
        $backend.Refresh()
        if ($backend.HasExited) {
            $details = if (Test-Path $stderrLog) { Get-Content $stderrLog -Raw } else { '' }
            throw "Django exited during startup.`n$details"
        }
        try {
            $response = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://${BackendHost}:${BackendPort}/api/v1/meta/"
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch {
            # Backend is still starting.
        }
    }
    if (-not $ready) {
        throw "Django did not become ready within 60 seconds. See $stderrLog"
    }

    Write-Host 'Django is ready. Starting Vite...' -ForegroundColor Green
    Push-Location (Join-Path $root 'client')
    try { & npm.cmd run dev } finally { Pop-Location }
} finally {
    if ($backend -and -not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    }
}
