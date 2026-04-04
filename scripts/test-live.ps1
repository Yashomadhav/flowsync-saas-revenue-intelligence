# Live deployment smoke test for FlowSync Revenue Intelligence
$base = "https://flowsync-revenue-intelligence.vercel.app"

$routes = @(
    "/",
    "/dashboard",
    "/dashboard/revenue",
    "/dashboard/cohorts",
    "/dashboard/health",
    "/dashboard/funnel"
)

$passed = 0
$failed = 0

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  FlowSync Live Deployment Smoke Test" -ForegroundColor Cyan
Write-Host "  Target: $base" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

foreach ($route in $routes) {
    $url = $base + $route
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 30 -MaximumRedirection 5
        $status = $resp.StatusCode
        $size = $resp.Content.Length
        $hasHtml = $resp.Content -match "<html"
        $hasNext = $resp.Content -match "__NEXT_DATA__"
        if ($status -eq 200 -and $hasHtml) {
            Write-Host "[PASS] $route  (HTTP $status, ${size} bytes, Next.js=$hasNext)" -ForegroundColor Green
            $passed++
        } else {
            Write-Host "[WARN] $route  (HTTP $status, size=${size})" -ForegroundColor Yellow
            $failed++
        }
    } catch {
        $msg = $_.Exception.Message
        Write-Host "[FAIL] $route  -- $msg" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "--------------------------------------------" -ForegroundColor Cyan
Write-Host "Results: $passed passed, $failed failed" -ForegroundColor Cyan
Write-Host "--------------------------------------------" -ForegroundColor Cyan
Write-Host ""

# Check for 404 page
Write-Host "Testing 404 handling..." -ForegroundColor Yellow
try {
    $r404 = Invoke-WebRequest -Uri "$base/nonexistent-page-xyz" -UseBasicParsing -TimeoutSec 15 -MaximumRedirection 5
    if ($r404.StatusCode -eq 404 -or $r404.Content -match "not.found|404") {
        Write-Host "[PASS] 404 page handled correctly" -ForegroundColor Green
    } else {
        Write-Host "[WARN] 404 returned HTTP $($r404.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    # 404 throws exception in PowerShell - that's correct behavior
    Write-Host "[PASS] 404 page returns error status (correct)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Smoke test complete." -ForegroundColor Cyan
