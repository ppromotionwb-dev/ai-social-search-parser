# Установка / обновление агента лидов на этом компьютере (отдельно от агента маркетплейсов — его скиллы здесь не ставятся).
# 1) скилл lidy-fb -> %USERPROFILE%\.claude\skills\lidy-fb (накопленное: outbox, sostoyanie, config.json, ПАУЗА.txt — не трогает)
# 2) config.json (адрес Пульта + токен агента лидов) из папки установщика — в скилл, если он лежит рядом
# 3) отправщик — в автозагрузку Windows (раз при входе: отправить то, что не ушло) и проверка связи с Пультом
$ErrorActionPreference = 'Stop'
$dst = Join-Path $env:USERPROFILE '.claude\skills'
New-Item -ItemType Directory -Force -Path $dst | Out-Null

foreach ($s in @('lidy-fb')) {
  $from = Join-Path $PSScriptRoot "skills\$s"
  $to = Join-Path $dst $s
  robocopy $from $to /E /XD 'outbox' 'sostoyanie' /XF 'config.json' 'ПАУЗА.txt' /NJH /NJS /NFL /NDL | Out-Null
  Write-Host "OK  скилл $s"
}
$skill = Join-Path $dst 'lidy-fb'

$cfgSrc = Join-Path $PSScriptRoot 'config.json'
$cfgDst = Join-Path $skill 'config.json'
if (Test-Path $cfgSrc) { Copy-Item $cfgSrc $cfgDst -Force; Write-Host 'OK  config.json' }
elseif (-not (Test-Path $cfgDst)) { Write-Host '!!  нет config.json: файл с адресом Пульта и токеном агента лидов выдаёт разработчик — положите рядом с install.ps1 и запустите ещё раз' -ForegroundColor Yellow }

# автозагрузка: при входе в Windows один раз отправить накопленное (без окна)
$startup = [Environment]::GetFolderPath('Startup')
$lnk = Join-Path $startup 'Агент лидов — отправка.lnk'
$sh = New-Object -ComObject WScript.Shell
$l = $sh.CreateShortcut($lnk)
$l.TargetPath = 'powershell.exe'
$l.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$skill\otpravka.ps1`" -Once"
$l.WindowStyle = 7
$l.Save()
Write-Host 'OK  отправщик в автозагрузке'

if (Test-Path $cfgDst) {
  $ErrorActionPreference = 'Continue'
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $skill 'otpravka.ps1') -Zaprosy
  $z = Join-Path $skill 'sostoyanie\zaprosy.json'
  if ((Test-Path $z) -and -not (([IO.File]::ReadAllText($z) | ConvertFrom-Json).offline)) { Write-Host 'OK  отправщик на связи с Пультом' }
  else { Write-Host '!!  Пульт не ответил — смотрите sostoyanie\otpravka.log в папке скилла' -ForegroundColor Yellow }
}
