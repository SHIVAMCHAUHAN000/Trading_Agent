# Copy the in-repo Hermes skill into ~/.hermes/skills for local Hermes Agent discovery.
$ErrorActionPreference = "Stop"

$repoSkill = Join-Path $PSScriptRoot "..\hermes\skills\quant-research\indian-market-strategy-research"
$repoSkill = (Resolve-Path $repoSkill).Path
$destRoot = Join-Path $HOME ".hermes\skills\quant-research\indian-market-strategy-research"

New-Item -ItemType Directory -Force -Path $destRoot | Out-Null
Copy-Item -Path (Join-Path $repoSkill "*") -Destination $destRoot -Recurse -Force

Write-Host "Installed Hermes skill to: $destRoot"
Write-Host "Restart Hermes / start a new session so the skill is discovered."
Write-Host "If Hermes is not installed yet, see docs/HERMES.md"
