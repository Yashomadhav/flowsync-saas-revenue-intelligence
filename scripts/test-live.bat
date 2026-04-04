@echo off
echo.
echo ============================================
echo   FlowSync Live Deployment Smoke Test
echo ============================================
echo.

set BASE=https://flowsync-revenue-intelligence.vercel.app

echo [1/7] Landing page /
curl.exe -s -o NUL -w "  Status: %%{http_code}  Size: %%{size_download} bytes  Time: %%{time_total}s\n" "%BASE%/"

echo [2/7] Executive Dashboard /dashboard
curl.exe -s -o NUL -w "  Status: %%{http_code}  Size: %%{size_download} bytes  Time: %%{time_total}s\n" "%BASE%/dashboard"

echo [3/7] Revenue Movements /dashboard/revenue
curl.exe -s -o NUL -w "  Status: %%{http_code}  Size: %%{size_download} bytes  Time: %%{time_total}s\n" "%BASE%/dashboard/revenue"

echo [4/7] Cohort Retention /dashboard/cohorts
curl.exe -s -o NUL -w "  Status: %%{http_code}  Size: %%{size_download} bytes  Time: %%{time_total}s\n" "%BASE%/dashboard/cohorts"

echo [5/7] Customer Health /dashboard/health
curl.exe -s -o NUL -w "  Status: %%{http_code}  Size: %%{size_download} bytes  Time: %%{time_total}s\n" "%BASE%/dashboard/health"

echo [6/7] Funnel and Growth /dashboard/funnel
curl.exe -s -o NUL -w "  Status: %%{http_code}  Size: %%{size_download} bytes  Time: %%{time_total}s\n" "%BASE%/dashboard/funnel"

echo [7/7] 404 handling /nonexistent-xyz
curl.exe -s -o NUL -w "  Status: %%{http_code}  Size: %%{size_download} bytes\n" "%BASE%/nonexistent-xyz"

echo.
echo ============================================
echo   Content validation checks
echo ============================================
echo.

echo Checking landing page contains FlowSync branding...
curl.exe -s "%BASE%/" | findstr /i "FlowSync" >NUL && echo   [PASS] FlowSync branding found || echo   [FAIL] FlowSync branding missing

echo Checking landing page contains Next.js data...
curl.exe -s "%BASE%/" | findstr /i "__NEXT_DATA__" >NUL && echo   [PASS] Next.js SSR data present || echo   [FAIL] Next.js SSR data missing

echo Checking dashboard contains Next.js data...
curl.exe -s "%BASE%/dashboard" | findstr /i "__NEXT_DATA__" >NUL && echo   [PASS] Dashboard Next.js SSR data present || echo   [FAIL] Dashboard SSR data missing

echo Checking revenue page contains Next.js data...
curl.exe -s "%BASE%/dashboard/revenue" | findstr /i "__NEXT_DATA__" >NUL && echo   [PASS] Revenue page Next.js SSR data present || echo   [FAIL] Revenue page SSR data missing

echo.
echo ============================================
echo   Smoke test complete
echo ============================================
