<#
.SYNOPSIS
  Copia de seguridad de la base de Bille: roles, esquema y datos (incluye las cuentas de auth).

.DESCRIPTION
  Usa `supabase db dump` (corre pg_dump en Docker, no hace falta instalarlo).
  Sin URL copia el Supabase local; para la nube definí BILLE_URL_BASE_DATOS_BACKUP con la cadena
  de conexión de Supabase (Settings -> Database), así la contraseña no queda en el historial.
  Cada copia queda en backups/AAAA-MM-DD_HHmm y se conservan las últimas -Conservar.

.EXAMPLE
  .\scripts\backup.ps1
.EXAMPLE
  $env:BILLE_URL_BASE_DATOS_BACKUP = "postgresql://postgres.xxxx:clave@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"
  .\scripts\backup.ps1 -Conservar 30
#>
param(
  [string]$Carpeta = (Join-Path $PSScriptRoot "..\backups"),
  [int]$Conservar = 14
)

$ErrorActionPreference = "Stop"
$raiz = Resolve-Path (Join-Path $PSScriptRoot "..")
$destino = Join-Path $Carpeta (Get-Date -Format "yyyy-MM-dd_HHmm")
New-Item -ItemType Directory -Force -Path $destino | Out-Null

$origen = if ($env:BILLE_URL_BASE_DATOS_BACKUP) { @("--db-url", $env:BILLE_URL_BASE_DATOS_BACKUP) } else { @("--local") }
$copias = @(
  @{ Archivo = "roles.sql"; Opciones = @("--role-only") },
  @{ Archivo = "esquema.sql"; Opciones = @() },
  @{ Archivo = "datos.sql"; Opciones = @("--data-only", "--use-copy") }
)

Push-Location $raiz
try {
  foreach ($copia in $copias) {
    $archivo = Join-Path $destino $copia.Archivo
    npx supabase db dump @origen @($copia.Opciones) --file $archivo
    if ($LASTEXITCODE -ne 0) { throw "Falló la copia de $($copia.Archivo)" }
    if ((Get-Item $archivo).Length -eq 0) { throw "La copia de $($copia.Archivo) quedó vacía" }
  }
} catch {
  Remove-Item -Recurse -Force $destino -ErrorAction SilentlyContinue
  throw
} finally {
  Pop-Location
}

# Rotación: borra las copias más viejas y deja las últimas $Conservar
Get-ChildItem -Directory $Carpeta | Sort-Object Name -Descending | Select-Object -Skip $Conservar |
  Remove-Item -Recurse -Force

Write-Host "Copia lista en $destino"
