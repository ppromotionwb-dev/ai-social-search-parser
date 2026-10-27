# Отправщик агента лидов на Пульт (пространство «Лиды»). Без ИИ, запускается скиллом и при входе в Windows.
#   -Zaprosy  скачать с Пульта запросы и паузу в sostoyanie\zaprosy.json (и заодно отправить накопленное)
#   -Once     отправить все файлы outbox\*.json на /api/leads/agent/ingest; ушедшие — в outbox\sent\<дата>\,
#             отвергнутые сервером (400/413) — в outbox\bad\; нет связи — файлы ждут следующего запуска
# Токен — в config.json рядом (выдаёт разработчик; это НЕ токен агента маркетплейсов). Повторная отправка безопасна.
param([switch]$Zaprosy, [switch]$Once, [string]$Config = (Join-Path $PSScriptRoot 'config.json'))

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$utf8 = New-Object System.Text.UTF8Encoding($false)
$ver = '2026-10-27'

$mutex = New-Object System.Threading.Mutex($false, 'Local\LeadAgentOtpravka')
if (-not $mutex.WaitOne(60000)) { exit 0 }

$outbox = Join-Path $PSScriptRoot 'outbox'
$sost = Join-Path $PSScriptRoot 'sostoyanie'
$log = Join-Path $sost 'otpravka.log'
New-Item -ItemType Directory -Force -Path $outbox, $sost, (Join-Path $outbox 'sent'), (Join-Path $outbox 'bad') | Out-Null

function Log($m) {
  try {
    if ((Test-Path $log) -and (Get-Item $log).Length -gt 1MB) { Move-Item $log ($log + '.old') -Force }
    [IO.File]::AppendAllText($log, (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '  ' + $m + "`r`n", $utf8)
  } catch {}
}
function Save-Zaprosy($obj) { [IO.File]::WriteAllText((Join-Path $sost 'zaprosy.json'), ($obj | ConvertTo-Json -Depth 5), $utf8) }

if (-not (Test-Path $Config)) {
  Log 'нет config.json — отправка невозможна'
  if ($Zaprosy) { Save-Zaprosy @{ offline = $true; reason = 'нет config.json'; queries = @(); pause = $null } }
  Write-Host '!!  нет config.json (адрес Пульта и токен агента лидов)'
  exit 1
}
$cfg = [IO.File]::ReadAllText($Config, $utf8) | ConvertFrom-Json
$url = $cfg.url.TrimEnd('/')
$headers = @{ Authorization = 'Bearer ' + $cfg.token }

function Post($path, $body) {
  Invoke-RestMethod -Method Post -Uri ($url + $path) -Headers $headers -ContentType 'application/json; charset=utf-8' -Body $body -TimeoutSec 60 -UserAgent "lead-agent/$ver"
}

# 1. накопленное — на Пульт
$sent = 0; $bad = 0; $wait = 0
foreach ($f in @(Get-ChildItem -Path $outbox -Filter '*.json' -File | Sort-Object Name)) {
  $body = [IO.File]::ReadAllBytes($f.FullName)
  try {
    $r = Post '/api/leads/agent/ingest' $body
    $day = Join-Path $outbox ('sent\' + (Get-Date -Format 'yyyy-MM-dd'))
    New-Item -ItemType Directory -Force -Path $day | Out-Null
    Move-Item $f.FullName (Join-Path $day $f.Name) -Force
    $sent++
    $rej = @($r.rejected).Count
    Log ("отправлен {0}: принято {1}, новых {2}{3}" -f $f.Name, $r.stored, $r.fresh, $(if ($rej) { ", отклонено $rej" } else { '' }))
  } catch {
    $code = 0; try { $code = [int]$_.Exception.Response.StatusCode } catch {}
    if ($code -eq 400 -or $code -eq 413) { Move-Item $f.FullName (Join-Path $outbox ('bad\' + $f.Name)) -Force; $bad++; Log "отклонён сервером ($code): $($f.Name)" }
    else { $wait++; Log "нет связи ($code): $($f.Name) ждёт — $($_.Exception.Message)"; break }
  }
}
if ($sent -or $bad -or $wait) { Write-Host "OK  отправлено $sent, отклонено $bad, ждут $wait" }
if ($code -eq 401) { Write-Host '!!  Пульт не принял токен: проверьте config.json' }

# 2. сигнал «на связи» и запросы с Пульта
try { [void](Post '/api/leads/agent/heartbeat' ('{"version":"' + $ver + '"}')) } catch { Log "heartbeat: $($_.Exception.Message)" }
if ($Zaprosy) {
  try {
    $q = Invoke-RestMethod -Uri ($url + '/api/leads/agent/queries') -Headers $headers -TimeoutSec 60 -UserAgent "lead-agent/$ver"
    Save-Zaprosy @{ offline = $false; at = (Get-Date).ToString('o'); queries = @($q.queries); pause = $q.pause }
    Write-Host ("OK  запросов с Пульта: {0}{1}" -f @($q.queries).Count, $(if ($q.pause) { ', ПАУЗА' } else { '' }))
  } catch {
    Save-Zaprosy @{ offline = $true; reason = $_.Exception.Message; queries = @(); pause = $null }
    Log "запросы: $($_.Exception.Message)"
    Write-Host '!!  Пульт недоступен — запросы по умолчанию'
  }
}
