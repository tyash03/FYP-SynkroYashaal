# FREE Whisper Transcription Setup Script
# Run this script to install all dependencies for local transcription

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Synkro - FREE Whisper Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if FFmpeg is installed
Write-Host "[1/3] Checking FFmpeg installation..." -ForegroundColor Yellow
$ffmpegInstalled = $false

try {
    $ffmpegVersion = ffmpeg -version 2>$null
    if ($LASTEXITCODE -eq 0) {
        $ffmpegInstalled = $true
        Write-Host "  ✓ FFmpeg is installed!" -ForegroundColor Green
    }
} catch {
    $ffmpegInstalled = $false
}

if (-not $ffmpegInstalled) {
    Write-Host "  ✗ FFmpeg not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Please install FFmpeg:" -ForegroundColor Yellow
    Write-Host "  Option 1: choco install ffmpeg" -ForegroundColor White
    Write-Host "  Option 2: Download from https://ffmpeg.org/download.html" -ForegroundColor White
    Write-Host ""
    Write-Host "  After installation, restart your terminal and run this script again." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Python version
Write-Host "[2/3] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python 3\.([0-9]+)") {
    $minorVersion = [int]$Matches[1]
    if ($minorVersion -ge 8) {
        Write-Host "  ✓ Python version OK: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Python 3.8+ required (found: $pythonVersion)" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "  ✗ Python not found or version could not be determined" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install Python packages
Write-Host "[3/3] Installing Python packages..." -ForegroundColor Yellow
Write-Host "  This will download about 500MB-1GB. Please be patient..." -ForegroundColor White
Write-Host ""

pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✓ Setup Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Start the server:" -ForegroundColor White
    Write-Host "     uvicorn app.main:app --reload" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  2. Upload a meeting recording" -ForegroundColor White
    Write-Host ""
    Write-Host "  3. Wait 2-5 minutes for FREE transcription to complete" -ForegroundColor White
    Write-Host ""
    Write-Host "Notes:" -ForegroundColor Cyan
    Write-Host "  • No API keys needed for transcription!" -ForegroundColor Green
    Write-Host "  • Transcription runs locally (FREE but slower)" -ForegroundColor Yellow
    Write-Host "  • First run downloads Whisper model (~150MB)" -ForegroundColor Yellow
    Write-Host "  • For summaries, add OPENAI_API_KEY to .env" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  ✗ Installation Failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the error messages above." -ForegroundColor Yellow
    Write-Host ""
}

Read-Host "Press Enter to exit"
