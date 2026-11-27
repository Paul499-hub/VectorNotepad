param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidatePattern('^(tests\.)?test_[A-Za-z0-9_]+$')]
    [string]$TestName
)

$module = $TestName
if ($module -notlike 'tests.*') {
    $module = "tests.$module"
}

$composeFile = Join-Path $PSScriptRoot 'docker-compose.cpu.test.yml'
$exitCode = 1

try {
    docker compose -f $composeFile up -d
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not start the CPU test stack.'
    }

    Write-Host 'Waiting for the CPU test backend...'
    $deadline = [DateTime]::UtcNow.AddMinutes(5)
    while ($true) {
        try {
            Invoke-WebRequest -Uri 'http://127.0.0.1:48726/' -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop | Out-Null
            break
        } catch {
            if ([DateTime]::UtcNow -ge $deadline) {
                docker compose -f $composeFile logs --tail 30 backend
                throw 'The CPU test backend did not become ready.'
            }
            Start-Sleep -Seconds 2
        }
    }

    docker compose -f $composeFile exec -T backend python -m $module -v
    $exitCode = $LASTEXITCODE
} catch {
    Write-Error $_ -ErrorAction Continue
} finally {
    docker compose -f $composeFile down
    if ($exitCode -eq 0 -and $LASTEXITCODE -ne 0) {
        $exitCode = $LASTEXITCODE
    }
}

exit $exitCode
