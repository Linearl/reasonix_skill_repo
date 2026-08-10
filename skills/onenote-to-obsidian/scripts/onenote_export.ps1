# OneNote .one 分区导出为页面 XML（OneNote COM API）
# 用法: powershell -ExecutionPolicy Bypass -File onenote_export.ps1 -OnePath "C:\path\xx.one" -OutDir "C:\out" [-PageInfo 0]
# 产出: <OutDir>/pages/NNNN.xml + <OutDir>/index.tsv（序号、页面ID、页面名）
# 注意: 本文件必须保持 UTF-8 with BOM；不要用 $pid 变量（保留变量）
param(
  [Parameter(Mandatory=$true)][string]$OnePath,
  [Parameter(Mandatory=$true)][string]$OutDir,
  [int]$PageInfo = 0,
  [int]$MaxPages = 0
)
$ErrorActionPreference = 'Continue'
if (-not (Test-Path $OnePath)) { Write-Output "错误: .one 文件不存在: $OnePath"; exit 1 }
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$pagesDir = Join-Path $OutDir 'pages'
New-Item -ItemType Directory -Path $pagesDir -Force | Out-Null

$one = New-Object -ComObject OneNote.Application
$hier = [ref]''
# cftLocal=0：打开本地 .one 文件（其他值报 0x80042018）
$one.OpenHierarchy($OnePath, '', $hier, 0) | Out-Null
$xml = [ref]''
# hsChildren=1：分区级必须用 1（3 返回 0 页面，2 报 0x80042014）
$one.GetHierarchy($hier.Value, 1, $xml) | Out-Null

$pages = [regex]::Matches($xml.Value, '<one:Page [^>]*>')
$index = New-Object System.Collections.Generic.List[string]
$i = 0
$fail = 0
foreach ($pm in $pages) {
  $tag = $pm.Value
  $idM = [regex]::Match($tag, 'ID="([^"]*)"')
  $nameM = [regex]::Match($tag, 'name="([^"]*)"')
  if (-not $idM.Success) { continue }
  $pageId = $idM.Groups[1].Value
  $pageName = if ($nameM.Success) { $nameM.Groups[1].Value } else { '' }
  $i++
  if ($MaxPages -gt 0 -and $i -gt $MaxPages) { $i--; break }
  $num = $i.ToString('D4')
  try {
    $content = [ref]''
    $one.GetPageContent($pageId, $content, $PageInfo) | Out-Null
    $content.Value | Out-File -FilePath (Join-Path $pagesDir ($num + '.xml')) -Encoding utf8
    $index.Add("$num`t$pageId`t$pageName")
  } catch {
    $fail++
    $index.Add("$num`t$pageId`t$pageName`tERROR")
  }
  if ($i % 25 -eq 0) { Write-Output "进度: $i / $($pages.Count) 失败:$fail" }
}
$index | Out-File -FilePath (Join-Path $OutDir 'index.tsv') -Encoding utf8
Write-Output "完成: 共 $i 页, 失败 $fail"
