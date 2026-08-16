param(
    [switch]$Organizer
)
# ============================================================
#  ReasonixSync 定时任务安装（PowerShell）
#   用法:  powershell -ExecutionPolicy Bypass -File install-tasks.ps1 [-Organizer]
#   普通用户即可（无需管理员）
#   所有任务启用 StartWhenAvailable：关机错过计划时间 → 开机后尽快补跑
#   Push = 每天 10:00（幂等，保证快照新鲜）
#   Pull = 每周一 10:30（错过 → 开机补跑）
#   Organize = 每周五 11:00（仅主力机，-Organizer 参数）
# ============================================================
$ErrorActionPreference = "Stop"

# ---- 定位 pythonw.exe ----
$pyw = $null
$candidates = @(
    "$env:USERPROFILE\anaconda3\pythonw.exe",
    "$env:USERPROFILE\miniconda3\pythonw.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\pythonw.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\pythonw.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\pythonw.exe",
    "$env:LOCALAPPDATA\Microsoft\WindowsApps\pythonw.exe"
)
foreach ($c in $candidates) {
    if (Test-Path $c) { $pyw = $c; break }
}
if (-not $pyw) {
    $cmd = Get-Command pythonw -ErrorAction SilentlyContinue
    if ($cmd) { $pyw = $cmd.Source }
}
if (-not $pyw) {
    Write-Host "[ERROR] pythonw.exe not found. Install Python or edit the candidate list in install-tasks.ps1"
    exit 1
}
Write-Host "Using pythonw: $pyw"

# ---- 定位 sync 根目录（本脚本位于 ...\ReasonixSync\scripts\ 下）----
$syncDir = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path "$syncDir\scripts\sync-push.py")) {
    Write-Host "[ERROR] scripts folder missing under $syncDir - is OneDrive fully synced?"
    exit 1
}
Write-Host "Sync dir: $syncDir"

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew

function New-RxTask {
    param([string]$Name, [string]$Script, $Trigger, [string[]]$Followup = @())
    # 主脚本 + 可选的后续脚本（同 trigger 依次执行，如 Pull 后跑 sync-feedback.py 生成检查/反馈模板）
    $actions = @()
    $actions += New-ScheduledTaskAction -Execute $pyw -Argument "`"$syncDir\scripts\$Script`""
    foreach ($f in $Followup) {
        $actions += New-ScheduledTaskAction -Execute $pyw -Argument "`"$syncDir\scripts\$f`""
    }
    Register-ScheduledTask -TaskName "ReasonixSync\$Name" -Action $actions -Trigger $Trigger -Settings $settings -Force | Out-Null
    Write-Host "Created: ReasonixSync\$Name  (StartWhenAvailable = True, Actions=$($actions.Count))"
}

# Push：每天 10:00（脚本幂等，无变更零成本；关机错过 → 开机补跑，保证本周快照新鲜）
New-RxTask -Name "Push" -Script "sync-push.py" -Trigger (New-ScheduledTaskTrigger -Daily -At 10:00)
# Pull：每周一 10:30（拿到 dist 主版本；错过 → 开机补跑）
# 跟随动作 sync-feedback.py：拉取后自动生成 feedback\pull-review-<周>-<本机名>.md 检查/反馈模板
# （各机填写后主力机 Organize 时可见，见 README「Pull 后检查与反馈」）
New-RxTask -Name "Pull" -Script "sync-pull.py" -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 10:30) -Followup @("sync-feedback.py")
if ($Organizer) {
    # Organize：仅主力机，每周五 11:00（汇总本周各机快照；错过 → 开机补跑）
    New-RxTask -Name "Organize" -Script "sync-organize.py" -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At 11:00)
}

Write-Host ""
Write-Host "Done. Verify with:  Get-ScheduledTask -TaskName 'ReasonixSync\*' | Select TaskName, State"
