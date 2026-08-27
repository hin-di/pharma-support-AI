Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  PharmaSupport AI - 共有用公開URL発行スクリプト" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. FastAPI サーバーが起動しているか確認
$serverPort = 8000
$isListening = Get-NetTCPConnection -LocalPort $serverPort -ErrorAction SilentlyContinue

if (-not $isListening) {
    Write-Host "[1/2] アプリケーションサーバー (FastAPI) を起動しています..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "main.py" -WindowStyle Minimized
    Start-Sleep -Seconds 2
} else {
    Write-Host "[1/2] アプリケーションサーバーは既に稼働中です。" -ForegroundColor Green
}

# 2. Cloudflare Tunnel の起動
Write-Host "[2/2] 共有用URLを発行中..." -ForegroundColor Yellow
Write-Host "※ 以下のログの中に表示される 'https://xxxx.trycloudflare.com' を共有してください。" -ForegroundColor White
Write-Host "※ 終了するときは Ctrl + C を押してください。" -ForegroundColor Gray
Write-Host "--------------------------------------------------------" -ForegroundColor Gray

.\cloudflared.exe tunnel --url http://localhost:8000
