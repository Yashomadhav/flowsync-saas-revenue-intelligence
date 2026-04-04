$results = @()
$endpoints = @(
    "http://localhost:8000/health",
    "http://localhost:8000/api/v1/executive/summary",
    "http://localhost:8000/api/v1/executive/mrr-trend",
    "http://localhost:8000/api/v1/executive/waterfall",
    "http://localhost:8000/api/v1/executive/by-plan",
    "http://localhost:8000/api/v1/executive/by-region",
    "http://localhost:8000/api/v1/executive/top-expanding",
    "http://localhost:8000/api/v1/executive/top-churn-risk",
    "http://localhost:8000/api/v1/revenue/mrr-bridge",
    "http://localhost:8000/api/v1/revenue/account-movements",
    "http://localhost:8000/api/v1/revenue/new-mrr-by-channel",
    "http://localhost:8000/api/v1/revenue/expansion-by-segment",
    "http://localhost:8000/api/v1/revenue/churned-by-plan",
    "http://localhost:8000/api/v1/revenue/payment-trend",
    "http://localhost:8000/api/v1/cohorts/heatmap",
    "http://localhost:8000/api/v1/cohorts/logo-churn-trend",
    "http://localhost:8000/api/v1/cohorts/nrr-by-cohort",
    "http://localhost:8000/api/v1/cohorts/retention-by-segment",
    "http://localhost:8000/api/v1/health/distribution",
    "http://localhost:8000/api/v1/health/churn-risk-quadrant",
    "http://localhost:8000/api/v1/health/risky-accounts",
    "http://localhost:8000/api/v1/health/support-burden",
    "http://localhost:8000/api/v1/funnel/overview",
    "http://localhost:8000/api/v1/funnel/conversion-by-channel",
    "http://localhost:8000/api/v1/funnel/sales-cycle",
    "http://localhost:8000/api/v1/funnel/expansion-by-segment"
)

foreach ($url in $endpoints) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 15
        $short = $r.Content.Substring(0, [Math]::Min(80, $r.Content.Length))
        $results += "OK  $($r.StatusCode)  $url  => $short"
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        $msg  = $_.Exception.Message
        $results += "ERR $code  $url  => $msg"
    }
}

$results | ForEach-Object { Write-Host $_ }
$results | Out-File "C:\Users\yasho\Desktop\endpoint_results.txt" -Encoding utf8
Write-Host "`nDone. Results saved to endpoint_results.txt"
