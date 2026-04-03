# =============================================================================
# FlowSync Revenue Intelligence — Local Development Startup Script (Windows)
# =============================================================================
# Usage:
#   .\scripts\start-local.ps1              # Start frontend only (mock data)
#   .\scripts\start-local.ps1 -Full        # Start full stack (requires Docker)
#   .\scripts\start-local.ps1 -Frontend    # Frontend only
#   .\scripts\start-local.ps1 -Backend     # Backend + DB only
#   .\scripts\start-local.ps1 -Generate    # Generate synthetic data
#   .\scripts\start-local.ps1 -Help        # Show help
# =============================================================================

param(
    [switch]$Full,
    [switch]$Frontend,
    [switch]$Backend,
    [switch]$Generate,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Colors
function Write-Header { param($msg) Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "  $msg" -ForegroundColor Gray }
function Write-Warn { param($msg) Write-Host "⚠ $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
if ($Help) {
    Write-Host @"

FlowSync Revenue Intelligence — Local Dev Startup
==================================================

USAGE:
  .\scripts\start-local.ps1 [flags]

FLAGS:
  (none)       Start frontend only with mock data (fastest, no Docker needed)
  -Full        Start full stack: PostgreSQL + FastAPI + Next.js via Docker Compose
  -Frontend    Start Next.js frontend only (mock data mode)
  -Backend     Start PostgreSQL + FastAPI only (requires Docker)
  -Generate    Generate synthetic data CSVs (requires Python)
  -Help        Show this help

QUICK START (no Docker):
  .\scripts\start-local.ps1
  → Opens http://localhost:3001 with mock data

FULL STACK (requires Docker Desktop):
  .\scripts\start-local.ps1 -Full
  → Starts all services, seeds database, opens http://localhost:3000

PREREQUISITES:
  - Node.js 18+ (for frontend)
  - Python 3.11+ (for data generation)
  - Docker Desktop (for full stack only)

"@
    exit 0
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
Write-Host @"

  ███████╗██╗      ██████╗ ██╗    ██╗███████╗██╗   ██╗███╗   ██╗ ██████╗
  ██╔════╝██║     ██╔═══██╗██║    ██║██╔════╝╚██╗ ██╔╝████╗  ██║██╔════╝
  █████╗  ██║     ██║   ██║██║ █╗ ██║███████╗ ╚████╔╝ ██╔██╗ ██║██║
  ██╔══╝  ██║     ██║   ██║██║███╗██║╚════██║  ╚██╔╝  ██║╚██╗██║██║
  ██║     ███████╗╚██████╔╝╚███╔███╔╝███████║   ██║   ██║ ╚████║╚██████╗
  ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝ ╚══════╝   ╚═╝   ╚═╝  ╚═══╝ ╚═════╝

  Revenue Intelligence Dashboard — Local Dev
"@ -ForegroundColor Blue

# ---------------------------------------------------------------------------
# Check prerequisites
# ---------------------------------------------------------------------------
Write-Header "Checking Prerequisites"

# Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Success "Node.js $nodeVersion"
} catch {
    Write-Err "Node.js not found. Install from https://nodejs.org"
    exit 1
}

# Python (optional)
try {
    $pyVersion = python --version 2>&1
    Write-Success "Python $pyVersion"
    $hasPython = $true
} catch {
    Write-Warn "Python not found — data generation will be skipped"
    $hasPython = $false
}

# Docker (optional)
try {
    $dockerVersion = docker --version 2>&1
    Write-Success "Docker: $dockerVersion"
    $hasDocker = $true
} catch {
    Write-Warn "Docker not found — full stack mode unavailable"
    $hasDocker = $false
}

# ---------------------------------------------------------------------------
# Generate synthetic data
# ---------------------------------------------------------------------------
if ($Generate) {
    Write-Header "Generating Synthetic Data"
    if (-not $hasPython) {
        Write-Err "Python required for data generation"
        exit 1
    }
    Set-Location "$ProjectRoot\data\generators"
    Write-Info "Running generate_all.py (300 accounts, 24 months)..."
    python generate_all.py
    Write-Success "Data generated in data/output/"
    Set-Location $ProjectRoot
    exit 0
}

# ---------------------------------------------------------------------------
# Full stack mode
# ---------------------------------------------------------------------------
if ($Full) {
    Write-Header "Starting Full Stack (Docker Compose)"
    if (-not $hasDocker) {
        Write-Err "Docker Desktop required for full stack mode"
        Write-Info "Install from https://www.docker.com/products/docker-desktop"
        exit 1
    }

    Set-Location $ProjectRoot

    # Copy env if not exists
    if (-not (Test-Path ".env")) {
        if (Test-Path "env.example") {
            Copy-Item "env.example" ".env"
            Write-Success "Created .env from env.example"
        }
    }

    Write-Info "Building and starting all services..."
    docker-compose up --build -d postgres api web

    Write-Info "Waiting for PostgreSQL to be healthy..."
    $retries = 0
    do {
        Start-Sleep -Seconds 3
        $health = docker-compose ps postgres 2>&1
        $retries++
        if ($retries -gt 20) {
            Write-Err "PostgreSQL failed to start after 60s"
            exit 1
        }
    } while ($health -notmatch "healthy")
    Write-Success "PostgreSQL is healthy"

    Write-Info "Generating synthetic data..."
    if ($hasPython) {
        Set-Location "$ProjectRoot\data\generators"
        python generate_all.py
        Set-Location $ProjectRoot
        Write-Success "Data generated"

        Write-Info "Running ingestion pipeline..."
        docker-compose --profile ingest up ingest
        Write-Success "Data ingested into PostgreSQL"
    }

    Write-Info "Running dbt transformations..."
    docker-compose --profile dbt run dbt dbt run
    Write-Success "dbt models built"

    Write-Host ""
    Write-Success "Full stack is running!"
    Write-Host ""
    Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  API:       http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
    Write-Host "  pgAdmin:   docker-compose --profile tools up pgadmin" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Stop:      docker-compose down" -ForegroundColor Gray
    Write-Host "  Logs:      docker-compose logs -f" -ForegroundColor Gray
    exit 0
}

# ---------------------------------------------------------------------------
# Backend only
# ---------------------------------------------------------------------------
if ($Backend) {
    Write-Header "Starting Backend (PostgreSQL + FastAPI)"
    if (-not $hasDocker) {
        Write-Err "Docker required for backend mode"
        exit 1
    }
    Set-Location $ProjectRoot
    docker-compose up --build -d postgres api
    Write-Success "Backend running at http://localhost:8000"
    Write-Info "API docs: http://localhost:8000/api/v1/docs"
    exit 0
}

# ---------------------------------------------------------------------------
# Frontend only (default) — mock data mode
# ---------------------------------------------------------------------------
Write-Header "Starting Frontend (Mock Data Mode)"

$webDir = "$ProjectRoot\apps\web"

# Install dependencies if needed
if (-not (Test-Path "$webDir\node_modules")) {
    Write-Info "Installing npm dependencies..."
    Set-Location $webDir
    npm install
    Write-Success "Dependencies installed"
}

# Set mock data env
$env:NEXT_PUBLIC_USE_MOCK_DATA = "true"
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000/api/v1"

Write-Info "Starting Next.js dev server on port 3001..."
Write-Host ""
Write-Host "  Landing page:  http://localhost:3001" -ForegroundColor Cyan
Write-Host "  Dashboard:     http://localhost:3001/dashboard" -ForegroundColor Cyan
Write-Host "  Revenue:       http://localhost:3001/dashboard/revenue" -ForegroundColor Cyan
Write-Host "  Cohorts:       http://localhost:3001/dashboard/cohorts" -ForegroundColor Cyan
Write-Host "  Health:        http://localhost:3001/dashboard/health" -ForegroundColor Cyan
Write-Host "  Funnel:        http://localhost:3001/dashboard/funnel" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

Set-Location $webDir
npm run dev
