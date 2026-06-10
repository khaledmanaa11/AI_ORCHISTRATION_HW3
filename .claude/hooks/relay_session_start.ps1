$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$root = $env:CLAUDE_PROJECT_DIR; if (-not $root) { $root = (Get-Location).Path }
$progress = Join-Path $root 'docs\PROGRESS.md'
Write-Output "=== RELAY STATE (auto-loaded - no tokens spent re-explaining) ==="
if (Test-Path $progress) {
  $lines = Get-Content $progress -Encoding UTF8
  $next = $lines | Where-Object { $_ -match 'NEXT:' } | Select-Object -First 1
  if ($next) { Write-Output $next }
  Write-Output "Open items:"
  $lines | Where-Object { $_ -match '^\s*- \[[ ~!]\]' } | Select-Object -First 6 | ForEach-Object { Write-Output $_ }
} else { Write-Output "(no docs/PROGRESS.md - run /relay-init)" }
Write-Output ""
Write-Output "=== Recent commits ==="
git -C $root log --oneline -5 2>$null
Write-Output "=== Director: say 'next' or run /relay-next to continue. ==="
