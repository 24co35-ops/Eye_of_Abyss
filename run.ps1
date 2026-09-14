<#
.SYNOPSIS
  Eye of Abyss — Developer & Operations helper script for Windows PowerShell
.EXAMPLE
  .\run.ps1 up
  .\run.ps1 down
  .\run.ps1 health
  .\run.ps1 dev-case-engine
#>

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Detect docker compose syntax (docker compose vs docker-compose)
$dockerComposeCmd = "docker compose"
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        $dockerComposeCmd = "docker-compose"
    }
}

switch ($Command.ToLower()) {
    "up" {
        Write-Host "Starting all services with Docker..." -ForegroundColor Cyan
        Invoke-Expression "$dockerComposeCmd -f infrastructure/docker-compose.yml up --build"
    }
    "down" {
        Write-Host "Stopping all services..." -ForegroundColor Yellow
        Invoke-Expression "$dockerComposeCmd -f infrastructure/docker-compose.yml down"
    }
    "build" {
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
        Write-Host "Running Case Engine dev server on port 8000..." -ForegroundColor Cyan
        Set-Location "services/case-engine"
        uvicorn main:app --reload --port 8000
    }
    "dev-voiceguard" {
        Write-Host "Running VoiceGuard dev server on port 8001..." -ForegroundColor Cyan
        Set-Location "services/voiceguard"
        uvicorn main:app --reload --port 8001
    }
    "dev-shadowtrace" {
        Write-Host "Running ShadowTrace dev server on port 8002..." -ForegroundColor Cyan
        Set-Location "services/shadowtrace"
        uvicorn main:app --reload --port 8002
    }
    "dev-chaineye" {
        Write-Host "Running ChainEye dev server on port 8003..." -ForegroundColor Cyan
        Set-Location "services/chaineye"
        uvicorn main:app --reload --port 8003
    }
    "frontend" {
        Write-Host "Starting Next.js frontend..." -ForegroundColor Cyan
        Set-Location "frontend"
        npm run dev
    }
    default {
        Write-Host "Eye of Abyss CLI helper" -ForegroundColor Cyan
        Write-Host "Usage: .\run.ps1 [command]"
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  up               - Build & start all containers (docker compose)"
        Write-Host "  down             - Stop containers"
        Write-Host "  build            - Build container images"
        Write-Host "  health           - Check HTTP health endpoints"
        Write-Host "  dev-case-engine  - Start Case Engine locally on :8000"
        Write-Host "  dev-voiceguard   - Start VoiceGuard locally on :8001"
        Write-Host "  dev-shadowtrace  - Start ShadowTrace locally on :8002"
        Write-Host "  dev-chaineye     - Start ChainEye locally on :8003"
        Write-Host "  frontend         - Start Next.js frontend on :3000"
    }
}
