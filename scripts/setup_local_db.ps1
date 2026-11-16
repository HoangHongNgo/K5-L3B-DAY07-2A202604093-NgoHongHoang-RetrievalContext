param([switch]$Stop)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$bin = Join-Path $root '.local\postgres\Library\bin'
$data = Join-Path $root '.local\pgdata'
$log = Join-Path $root '.local\postgres.log'
$envFile = Join-Path $root 'starter\.env'
if (-not (Test-Path -LiteralPath (Join-Path $bin 'pg_ctl.exe'))) {
    throw 'Local PostgreSQL is missing from .local/postgres.'
}
$env:PATH = "$bin;$env:PATH"
if ($Stop) {
    if (Test-Path -LiteralPath (Join-Path $data 'PG_VERSION')) {
        & pg_ctl.exe -D $data stop -m fast
    }
    exit $LASTEXITCODE
}
$urlLine = Get-Content -LiteralPath $envFile | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
if (-not $urlLine) { throw 'DATABASE_URL is missing from starter/.env.' }
$uri = [uri]$urlLine.Substring('DATABASE_URL='.Length)
if ($uri.Host -ne '127.0.0.1' -or $uri.Port -ne 55433 -or $uri.AbsolutePath -ne '/day6_lab') {
    throw 'Expected local day6_lab at 127.0.0.1:55433.'
}
$parts = $uri.UserInfo.Split(':', 2)
if ($parts.Count -ne 2) { throw 'DATABASE_URL needs user and password.' }
$password = [uri]::UnescapeDataString($parts[1])
$passwordFile = Join-Path $root '.local\pg-password.tmp'
$priorPassword = $env:PGPASSWORD
try {
    $env:PGPASSWORD = $password
    if (-not (Test-Path -LiteralPath (Join-Path $data 'PG_VERSION'))) {
        Set-Content -LiteralPath $passwordFile -Value $password -Encoding ascii -NoNewline
        & initdb.exe -D $data -U $parts[0] -A scram-sha-256 --encoding=UTF8 --locale=C "--pwfile=$passwordFile" --no-instructions
        if ($LASTEXITCODE -ne 0) { throw 'initdb failed.' }
    }
    & pg_ctl.exe -D $data status *> $null
    if ($LASTEXITCODE -ne 0) {
        & pg_ctl.exe -D $data -o '-h 127.0.0.1 -p 55433' -l $log start
        if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL failed to start.' }
    }
    $exists = & psql.exe -h 127.0.0.1 -p 55433 -U $parts[0] -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'day6_lab'"
    if ($LASTEXITCODE -ne 0) { throw 'Could not inspect PostgreSQL.' }
    if ($exists -ne '1') {
        & createdb.exe -h 127.0.0.1 -p 55433 -U $parts[0] day6_lab
        if ($LASTEXITCODE -ne 0) { throw 'Could not create day6_lab.' }
    }
    & psql.exe -h 127.0.0.1 -p 55433 -U $parts[0] -d day6_lab -c 'CREATE EXTENSION IF NOT EXISTS vector;'
    if ($LASTEXITCODE -ne 0) { throw 'Could not enable pgvector.' }
    Write-Output 'Local PostgreSQL is ready.'
} finally {
    Remove-Item -LiteralPath $passwordFile -Force -ErrorAction SilentlyContinue
    $env:PGPASSWORD = $priorPassword
}
