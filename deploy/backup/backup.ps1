param([string]$BackupDirectory = "storage/backups", [string]$AttachmentDirectory = "storage/attachments")
$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$backupRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../.." $BackupDirectory))
$attachmentRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../.." $AttachmentDirectory))
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
$envFile = Join-Path ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../.."))) ".env"
$config = @{}
if (Test-Path -LiteralPath $envFile) { Get-Content -LiteralPath $envFile | Where-Object { $_ -match '^[A-Za-z_][A-Za-z0-9_]*=' } | ForEach-Object { $key,$value = $_ -split '=',2; $config[$key]=$value } }
$databaseUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } elseif ($config.POSTGRES_USER) { $config.POSTGRES_USER } else { "pengka" }
$databaseName = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } elseif ($config.POSTGRES_DB) { $config.POSTGRES_DB } else { "pengka_material" }
$dbFile = Join-Path $backupRoot "db_$stamp.dump"
$attachmentFile = Join-Path $backupRoot "attachments_$stamp.tar.gz"
$manifestFile = Join-Path $backupRoot "backup_manifest_$stamp.json"
docker compose exec -T db pg_dump -U $databaseUser -d $databaseName -Fc | Set-Content -AsByteStream -Path $dbFile
tar -czf $attachmentFile -C $attachmentRoot .
$manifest = @{ timestamp=$stamp; database=(Split-Path $dbFile -Leaf); database_sha256=(Get-FileHash $dbFile -Algorithm SHA256).Hash; attachments=(Split-Path $attachmentFile -Leaf); attachments_sha256=(Get-FileHash $attachmentFile -Algorithm SHA256).Hash }
$manifest | ConvertTo-Json | Set-Content -Encoding UTF8 -Path $manifestFile
Write-Host "Backup completed: $manifestFile"
