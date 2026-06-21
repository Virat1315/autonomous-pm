# Deploy all 6 Autonomous PM backend services to Render via CLI.
# Prerequisites: render login, gh auth login, repo pushed to GitHub.
#
# Usage: .\scripts\deploy-render.ps1 -RepoUrl "https://github.com/YOUR_USER/autonomous-pm"

param(
    [string]$RepoUrl = "",
    [string]$Branch = "main",
    [string]$RenderCli = "$env:LOCALAPPDATA\render\cli_v2.20.0.exe",
    [string]$EnvFile = "$PSScriptRoot\..\.env",
    [string]$CorsOrigin = "https://web-dashboard-azure.vercel.app"
)

$ErrorActionPreference = "Stop"

function Read-DotEnv($path) {
    $vars = @{}
    if (-not (Test-Path $path)) { throw "Missing .env at $path" }
    Get-Content $path | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
        if ($_ -match '^([^=]+)=(.*)$') {
            $vars[$Matches[1].Trim()] = $Matches[2].Trim()
        }
    }
    return $vars
}

if (-not $RepoUrl) {
    $remote = git -C "$PSScriptRoot\.." remote get-url origin 2>$null
    if ($remote -match 'github\.com[:/](.+?)(?:\.git)?$') {
        $RepoUrl = "https://github.com/$($Matches[1])"
    } else {
        throw "Pass -RepoUrl or set git remote origin"
    }
}

$envVars = Read-DotEnv $EnvFile
$mongo = $envVars["MONGODB_URI"]
$gemini = $envVars["GEMINI_API_KEY"]
if (-not $mongo -or $mongo -match '\.\.\.') { throw "Set MONGODB_URI in .env" }
if (-not $gemini -or $gemini -match '\.\.\.') { throw "Set GEMINI_API_KEY in .env" }

$render = $RenderCli
if (-not (Test-Path $render)) { throw "Render CLI not found at $render" }

$common = @("--confirm", "--output", "json", "--branch", $Branch, "--repo", $RepoUrl, "--plan", "free", "--region", "oregon", "--auto-deploy", "yes", "--health-check-path", "/health")

function New-RenderService($name, $type, $runtime, $rootDir, $extraEnv) {
    $args = @("services", "create", "--name", $name, "--type", $type, "--runtime", $runtime) + $common
    if ($rootDir) { $args += @("--root-directory", $rootDir) }
    foreach ($pair in $extraEnv) { $args += @("--env-var", $pair) }
    Write-Host "`n>>> Creating $name ..."
    & $render @args
    if ($LASTEXITCODE -ne 0) { throw "Failed to create $name" }
}

# 1. Ticket service
New-RenderService "apm-ticket-service" "web_service" "docker" "services/ticket-service" @(
    "DATABASE_BACKEND=mongo",
    "MONGODB_URI=$mongo",
    "MONGODB_DBNAME=autonomous_pm",
    "PORT=3001",
    "LOG_LEVEL=info",
    "CORS_ORIGINS=$CorsOrigin"
)

$ticketUrl = "https://apm-ticket-service.onrender.com"

# 2. Priority (repo root — use Blueprint for dockerContext; CLI may need manual dashboard fix)
Write-Host "`n>>> Priority/standup services: use Render Blueprint (render.yaml) for repo-root Docker context."
Write-Host "    Dashboard: https://dashboard.render.com/blueprints -> New Blueprint -> connect repo -> Deploy"
Write-Host "    When prompted for secrets, enter MONGODB_URI and GEMINI_API_KEY from .env"

# 3. Update Vercel
Write-Host "`n>>> After ticket-service is live, run:"
Write-Host "    cd apps/web-dashboard"
Write-Host "    echo $ticketUrl | vercel env add TICKET_SERVICE_URL production"
Write-Host "    vercel deploy --prod"

Write-Host "`nDone (ticket-service via CLI). Deploy remaining 5 via Blueprint for correct Docker build context."
