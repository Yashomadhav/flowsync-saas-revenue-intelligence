# Full endpoint test suite — writes results to Desktop\endpoint_results.txt
$base = "http://localhost:8000/api/v1"
$results = @()

$endpoints = @(
    # Executive
    "$base/executive/summary",
    "$base/executive/mrr-trend",
    "$base/executive/waterfall",
    "$base/executive/by-plan",
    "$base/executive/by-region",
    "$base/executive/by-industry",
    "$base/executive/by-company-size",
    "$base/executive/top-expanding",
    "$base/executive/top-churn-risk",
    # Revenue
    "$base/revenue/mrr-bridge",
    "$base/revenue/account-movements",
    "$base/revenue/new-mrr-by-channel",
    "$base/revenue/expansion-by-segment",
    "$base/revenue/churned-by-plan",
    "$base/revenue/payment-trend",
    # Cohorts
    "$base/cohorts/heatmap",
    "$base/cohorts/logo-churn-trend",
    "$base/cohorts/nrr-by-cohort",
    "$base/cohorts/retention-by-segment",
    # Health
    "$base/health/distribution",
    "$base/health/churn-risk-quadrant",
    "$base/health/risky-accounts",
    "$base/health/support-burden",
    # Funnel
    "$base/funnel/overview",
    "$base/funnel/conversion-by-channel",
    "$base/funnel/sales-cycle",
    "$base/funnel/expansion-by-segment"
)

$pass = 0
$fail = 0

foreach ($url in $endpoints) {
    $path = ($url -replace ".*api/v1/","")
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 15
        $preview = $r.Content.Substring(0, [Math]::Min(80, $r.Content.Length)) -replace "`n",""
        $line = "PASS [$($r.StatusCode)] /$path => $preview..."
        $pass++
    } catch {
        $line = "FAIL /$path => $($_.Exception.Message)"
        $fail++
    }
    $results += $line
    Write-Host $line
}

$results += ""
$results += "=== SUMMARY: $pass PASS / $fail FAIL / $($endpoints.Count) TOTAL ==="
Write-Host ""
Write-Host "=== SUMMARY: $pass PASS / $fail FAIL / $($endpoints.Count) TOTAL ==="

$results | Out-File "C:\Users\yasho\Desktop\endpoint_results.txt" -Encoding utf8
Write-Host "Results saved to Desktop\endpoint_results.txt"
