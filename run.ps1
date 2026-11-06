<#
.SYNOPSIS
  Eye of Abyss — Developer & Operations helper script for Windows PowerShell
.EXAMPLE
  .\run.ps1 doctor
  .\run.ps1 up
  .\run.ps1 dev-backend
  .\run.ps1 frontend
#>

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# ponytail: stdlib PowerShell detection, no external wrappers or heavy modules
$root = $PSScriptRoot
$hasDocker = [bool](Get-Command docker -ErrorAction SilentlyContinue)
$hasDockerCompose = [bool](Get-Command docker-compose -ErrorAction SilentlyContinue)

if ($hasDocker) {
    $dockerComposeCmd = "docker compose"
} elseif ($hasDockerCompose) {
    $dockerComposeCmd = "docker-compose"
} else {
    $dockerComposeCmd = $null
}

function Assert-DockerInstalled {
    if (-not $dockerComposeCmd) {
        Write-Host "`n[ERROR] Docker is not installed or not found in system PATH." -ForegroundColor Red
        Write-Host "Containerized commands ('up', 'down', 'build') require Docker Desktop." -ForegroundColor Yellow
        Write-Host "Download: https://www.docker.com/products/docker-desktop/`n" -ForegroundColor Yellow
        Write-Host "Local alternative (without Docker):" -ForegroundColor Cyan
        Write-Host "  1. .\run.ps1 doctor           (Validate local environment)" -ForegroundColor Cyan
        Write-Host "  2. .\run.ps1 dev-case-engine  (Start backend on port 8000)" -ForegroundColor Cyan
        Write-Host "  3. .\run.ps1 frontend         (Start UI on port 3000)`n" -ForegroundColor Cyan
        exit 1
    }
}

function Run-PythonService([string]$path, [int]$port) {
    $svcPath = Join-Path $root $path
    if (!(Test-Path $svcPath)) {
        Write-Host "[ERROR] Directory not found: $svcPath" -ForegroundColor Red
        return
    }
    # ponytail: Push/Pop location prevents mutating developer's shell directory
    Push-Location $svcPath
    try {
        $env:PYTHONPATH = "$root;$root\shared;$svcPath"
        Write-Host "Starting service at $svcPath on port $port..." -ForegroundColor Cyan
        uvicorn main:app --reload --port $port
    } finally {
        Pop-Location
    }
}

switch ($Command.ToLower()) {
    "doctor" {
        Write-Host "`n=== Eye of Abyss Environment Diagnostic ===" -ForegroundColor Cyan
        
        # 1. Docker
        if ($dockerComposeCmd) {
            $dockerVer = & ($dockerComposeCmd.Split(' ')[0]) --version 2>$null
            Write-Host "[+] Docker: Detected ($dockerVer)" -ForegroundColor Green
            # Check if engine daemon is responsive
            $daemonCheck = & docker info 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[+] Docker Daemon: Running" -ForegroundColor Green
            } else {
                Write-Host "[-] Docker Daemon: NOT running. Start Docker Desktop." -ForegroundColor Yellow
            }
        } else {
            Write-Host "[-] Docker: NOT installed or not in PATH." -ForegroundColor Red
        }

        # 2. Python
        $py = Get-Command python -ErrorAction SilentlyContinue
        if ($py) {
            $pyVer = & python --version 2>&1
            Write-Host "[+] Python: $pyVer ($($py.Source))" -ForegroundColor Green
        } else {
            Write-Host "[-] Python: NOT found in PATH" -ForegroundColor Red
        }

        # 3. Node.js & npm
        $node = Get-Command node -ErrorAction SilentlyContinue
        $npm = Get-Command npm -ErrorAction SilentlyContinue
        if ($node -and $npm) {
            $nodeVer = & node -v
            Write-Host "[+] Node.js: $nodeVer | npm: $(& npm -v)" -ForegroundColor Green
        } else {
            Write-Host "[-] Node.js/npm: NOT found in PATH (required for frontend)" -ForegroundColor Red
        }

        # 4. .env Configuration & Security Check
        $envFile = Join-Path $root ".env"
        if (Test-Path $envFile) {
            Write-Host "[+] .env: Present" -ForegroundColor Green
            $content = Get-Content $envFile -Raw
            $weakKeys = @()
            if ($content -match "POSTGRES_PASSWORD=changeme") { $weakKeys += "POSTGRES_PASSWORD (changeme)" }
            if ($content -match "NEO4J_PASSWORD=changeme") { $weakKeys += "NEO4J_PASSWORD (changeme)" }
            if ($content -match "MINIO_ROOT_PASSWORD=minioadmin") { $weakKeys += "MINIO_ROOT_PASSWORD (minioadmin)" }
            if ($content -match "SEED_OWNER_PASSWORD=1234567890|SEED_OWNER_PASSWORD=changeme") { $weakKeys += "SEED_OWNER_PASSWORD" }
            
            if ($weakKeys.Count -gt 0) {
                Write-Host "[!] SECURITY WARNING: Default credentials detected in .env:" -ForegroundColor Yellow
                foreach ($wk in $weakKeys) {
                    Write-Host "    - $wk" -ForegroundColor Yellow
                }
                Write-Host "    Update .env with strong secrets before deploying to production." -ForegroundColor Yellow
            } else {
                Write-Host "[+] .env Secrets: No obvious default placeholders" -ForegroundColor Green
            }
        } else {
            Write-Host "[-] .env: MISSING. Run 'Copy-Item .env.example .env' and configure secrets." -ForegroundColor Red
        }
        Write-Host "============================================`n" -ForegroundColor Cyan
    }
    "up" {
        Assert-DockerInstalled
        Write-Host "Starting all services with Docker..." -ForegroundColor Cyan
        Invoke-Expression "$dockerComposeCmd -f infrastructure/docker-compose.yml up --build"
    }
    "down" {
        Assert-DockerInstalled
        Write-Host "Stopping all services..." -ForegroundColor Yellow
        Invoke-Expression "$dockerComposeCmd -f infrastructure/docker-compose.yml down"
    }
    "build" {
        Assert-DockerInstalled
        Write-Host "Building Docker images..." -ForegroundColor Cyan
        Invoke-Expression "$dockerComposeCmd -f infrastructure/docker-compose.yml build"
    }
    "health" {
        Write-Host "Checking service health..." -ForegroundColor Cyan
        $services = @(
            @{ Name = "Case Engine "; Url = "http://localhost:8000/health" },
            @{ Name = "VoiceGuard  "; Url = "http://localhost:8001/health" },
            @{ Name = "ShadowTrace "; Url = "http://localhost:8002/health" },
            @{ Name = "ChainEye    "; Url = "http://localhost:8003/health" }
        )
        foreach ($s in $services) {
            try {
                $res = Invoke-RestMethod -Uri $s.Url -Method Get -TimeoutSec 2 -ErrorAction Stop
                Write-Host "$($s.Name): OK ($($res.service))" -ForegroundColor Green
            } catch {
                Write-Host "$($s.Name): OFFLINE" -ForegroundColor Red
            }
        }
    }
    "dev-case-engine" {
        Run-PythonService "services/case-engine" 8000
    }
    "dev-voiceguard" {
        Run-PythonService "services/voiceguard" 8001
    }
    "dev-shadowtrace" {
        Run-PythonService "services/shadowtrace" 8002
    }
    "dev-chaineye" {
        Run-PythonService "services/chaineye" 8003
    }
    "frontend" {
        $frontendPath = Join-Path $root "frontend"
        Push-Location $frontendPath
        try {
            Write-Host "Starting Next.js frontend on port 3000..." -ForegroundColor Cyan
            npm run dev
        } finally {
            Pop-Location
        }
    }
    default {
        Write-Host "`nEye of Abyss CLI helper" -ForegroundColor Cyan
        Write-Host "Usage: .\run.ps1 [command]`n"
        Write-Host "Diagnostics & Setup:"
        Write-Host "  doctor           - Validate installed tools, Docker, and .env security"
        Write-Host "`nDocker Mode:"
        Write-Host "  up               - Build & start all containers (docker compose)"
        Write-Host "  down             - Stop containers"
        Write-Host "  build            - Build container images"
        Write-Host "  health           - Check HTTP health endpoints"
        Write-Host "`nLocal Development Mode (Without Docker):"
        Write-Host "  dev-case-engine  - Start Case Engine locally on :8000 (SQLite dev fallback)"
        Write-Host "  dev-voiceguard   - Start VoiceGuard locally on :8001"
        Write-Host "  dev-shadowtrace  - Start ShadowTrace locally on :8002"
        Write-Host "  dev-chaineye     - Start ChainEye locally on :8003"
        Write-Host "  frontend         - Start Next.js frontend on :3000`n"
    }
}
