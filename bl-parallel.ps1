<#
.SYNOPSIS
    Launch a parallel BrickLayer 2.0 campaign using Windows Terminal split panes.
    Each pane runs an independent Claude worker claiming questions from the shared queue.

.PARAMETER Project
    Project folder name under Bricklayer2.0/ (e.g. "adbp", "adbp3")

.PARAMETER Workers
    Number of parallel worker panes to open (default: 3, max: 6)

.PARAMETER Branch
    Git branch tag suffix (default: auto-generated from date, e.g. "mar20")

.EXAMPLE
    ./bl-parallel.ps1 -Project adbp -Workers 3
    ./bl-parallel.ps1 -Project adbp -Workers 2 -Branch mar20

.NOTES
    Requirements:
    - Windows Terminal (wt.exe) -- install from Microsoft Store if missing
    - Git Bash must be available as a WT profile named "Git Bash"
    - Project must have questions.md with PENDING questions
    - Run from the Bricklayer2.0 root directory
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Project,

    [ValidateRange(2, 6)]
    [int]$Workers = 3,

    [string]$Branch = ""
)

$ErrorActionPreference = "Stop"

# --- Paths ---
$BLRoot = "C:/Users/trg16/Dev/Bricklayer2.0"
$ProjectPath = Join-Path $BLRoot $Project
$ClaimPy = Join-Path $BLRoot "bl/claim.py"
$ParallelMd = Join-Path $BLRoot "template/program-parallel.md"

# --- Validate ---
if (-not (Test-Path $ProjectPath)) {
    Write-Error "Project not found: $ProjectPath"
    exit 1
}

if (-not (Test-Path (Join-Path $ProjectPath "questions.md"))) {
    Write-Error "No questions.md in $ProjectPath -- run /bl-questions first"
    exit 1
}

$wt = Get-Command wt.exe -ErrorAction SilentlyContinue
if (-not $wt) {
    Write-Error "Windows Terminal (wt.exe) not found. Install from the Microsoft Store."
    exit 1
}

# --- Branch setup ---
if ($Branch -eq "") {
    $Branch = (Get-Date).ToString("MMMdd").ToLower()
}
$BranchName = "$Project/$Branch-parallel"

# Check how many PENDING questions exist
$pendingCount = (python $ClaimPy pending $ProjectPath 2>$null | Measure-Object -Line).Lines
Write-Host ""
Write-Host "BrickLayer Parallel Launcher"
Write-Host "=============================="
Write-Host "  Project   : $Project"
Write-Host "  Workers   : $Workers"
Write-Host "  Branch    : $BranchName"
Write-Host "  Pending Q : $pendingCount"
Write-Host "  Claims    : $ProjectPath/claims.json"
Write-Host ""

if ($pendingCount -eq 0) {
    Write-Warning "No PENDING questions found in questions.md. Nothing to run."
    exit 0
}

# --- Copy program-parallel.md if needed ---
$destMd = Join-Path $ProjectPath "program-parallel.md"
if (-not (Test-Path $destMd)) {
    Copy-Item $ParallelMd $destMd
    Write-Host "Copied program-parallel.md to project"
}

# --- Setup branch (lead worker creates it) ---
Write-Host "Setting up branch $BranchName..."
$currentBranch = git -C $ProjectPath rev-parse --abbrev-ref HEAD 2>$null
if ($currentBranch -ne $BranchName) {
    $branchExists = git -C $BLRoot branch --list $BranchName
    if ($branchExists) {
        Write-Host "  Branch exists, workers will checkout: $BranchName"
    } else {
        $null = git -C $BLRoot checkout -b $BranchName 2>&1
        Write-Host "  Created branch: $BranchName"
    }
}

# --- Write per-worker prompt + launcher scripts ---
# Using .sh files per worker avoids PowerShell -> wt.exe -> bash escaping issues
$promptDir = Join-Path $ProjectPath ".parallel-prompts"
New-Item -ItemType Directory -Force -Path $promptDir | Out-Null

$projectPathFwd = $ProjectPath -replace '\\', '/'
$claimPyFwd     = $ClaimPy     -replace '\\', '/'

for ($i = 1; $i -le $Workers; $i++) {
    $promptFile  = (Join-Path $promptDir "worker-$i.txt")  -replace '\\', '/'
    $scriptFile  = (Join-Path $promptDir "worker-$i.sh")   -replace '\\', '/'

    # Write the prompt text file
    $prompt = @"
Read program-parallel.md and questions.md. You are BL worker $i of $Workers on project $Project.

Your environment:
  BL_WORKER_ID = $i
  Project path = $projectPathFwd
  Claims tool  = python $claimPyFwd

Begin the parallel research loop from program-parallel.md immediately.
The first thing you do is: python $claimPyFwd pending $projectPathFwd
Claim the first available question and start working.

NEVER STOP until python $claimPyFwd pending $projectPathFwd returns empty AND all your claimed questions are complete.
"@
    $prompt | Out-File -FilePath ($promptFile -replace '/', '\') -Encoding utf8 -NoNewline

    # Write the launcher .sh script — no inline escaping needed
    # Note: backtick-$ (`$) escapes PowerShell expansion, producing literal $ in the .sh file
    $script = @"
#!/bin/bash
cd '$projectPathFwd'
export BL_WORKER_ID=$i
git checkout $BranchName 2>/dev/null || true
PROMPT=`$(cat '$promptFile')
claude --dangerously-skip-permissions "`$PROMPT"
echo ''
echo 'Worker $i finished. Press Enter to close.'
read
"@
    $script | Out-File -FilePath ($scriptFile -replace '/', '\') -Encoding utf8 -NoNewline
}

Write-Host "Worker scripts written to $promptDir"
Write-Host ""

# --- Build Windows Terminal command ---
# Each pane just runs: bash /path/to/worker-N.sh
# No inline command escaping -- the .sh file handles everything

$wtParts = @()

for ($i = 1; $i -le $Workers; $i++) {
    $scriptFile = (Join-Path $promptDir "worker-$i.sh") -replace '\\', '/'
    $label = "BL-$Project-W$i"

    if ($i -eq 1) {
        $wtParts += "new-tab --title `"$label`" -p `"Git Bash`" -- bash `"$scriptFile`""
    } else {
        $wtParts += "; split-pane --title `"$label`" -p `"Git Bash`" -- bash `"$scriptFile`""
    }
}

# Status monitor pane
$monitorScript = (Join-Path $promptDir "monitor.sh") -replace '\\', '/'
$monitorScriptContent = @"
#!/bin/bash
cd '$projectPathFwd'
watch -n 10 python '$claimPyFwd' status .
"@
$monitorScriptContent | Out-File -FilePath ($monitorScript -replace '/', '\') -Encoding utf8 -NoNewline
$wtParts += "; split-pane --size 0.2 --title `"BL-Claims`" -p `"Git Bash`" -- bash `"$monitorScript`""

$wtArgString = $wtParts -join " "

Write-Host "Launching Windows Terminal with $Workers worker panes + claims monitor..."
Write-Host ""

# Launch
Start-Process "wt.exe" -ArgumentList $wtArgString

Write-Host "Workers launched. Monitor claims at:"
Write-Host "  python $ClaimPy status $ProjectPath"
Write-Host ""
Write-Host "To release a stuck claim:"
Write-Host "  python $ClaimPy release $ProjectPath {question_id}"
