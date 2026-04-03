# SaaS Revenue Intelligence Dashboard — Build Tracker

## Phase 1: Monorepo Init & Root Config ✅
- [x] TODO.md
- [x] README.md
- [x] env.example
- [x] .gitignore
- [x] docker-compose.yml (postgres:16, pgAdmin, api, web, dbt, seeder, ingest, validate)
- [x] Makefile (Unix/Mac)
- [x] scripts/start-local.ps1 (Windows PowerShell)
- [x] docs/architecture.md
- [x] docs/metrics-glossary.md
- [x] .github/workflows/ci.yml
- [x] .github/workflows/dbt-run.yml

## Phase 2: Data Layer ✅
- [x] docker/postgres/init.sql
- [x] docker/api.Dockerfile
- [x] docker/web.Dockerfile
- [x] database/migrations/001_create_schemas.sql (raw/staging/marts schemas, roles, audit_log)
- [x] database/migrations/002_raw_tables.sql (raw.* tables with TEXT cols + metadata)
- [x] database/migrations/003_staging_tables.sql (staging.stg_* typed tables)
- [x] database/migrations/004_marts_tables.sql (marts.fct_* and mart_* tables)
- [x] database/migrations/005_views_and_functions.sql (8 views + 4 functions)
- [x] database/schema.sql (master init using \ir)
- [x] data/generators/config.py
- [x] data/generators/generate_plans.py
- [x] data/generators/generate_features.py
- [x] data/generators/build_calendar.py
- [x] data/generators/generate_accounts.py
- [x] data/generators/generate_subscriptions.py
- [x] data/generators/generate_invoices.py
- [x] data/generators/generate_leads.py
- [x] data/generators/generate_usage_events.py
- [x] data/generators/generate_support_tickets.py
- [x] data/generators/load_raw_to_postgres.py
- [x] data/generators/generate_all.py
- [x] scripts/seed_db.py
- [x] scripts/ingest/ingest_pipeline.py (batch inserts, ON CONFLICT upserts, CLI args)
- [x] scripts/ingest/validate_counts.py (27 checks, --fail-fast, --output json/text)
- [x] scripts/ingest/__init__.py
- [x] dbt_project/dbt_project.yml
- [x] dbt_project/profiles.yml
- [x] dbt_project/models/bronze/ (6 models: accounts, subscriptions, invoices, usage_events, tickets, leads)
- [x] dbt_project/models/silver/ (6 models: stg_*)
- [x] dbt_project/models/gold/ (6 models: fct_mrr_movements, fct_account_monthly_health, fct_customer_cohorts, fct_sales_conversion, mart_exec_revenue_summary, mart_customer_success_summary)

## Phase 3: FastAPI Backend ✅
- [x] apps/api/__init__.py
- [x] apps/api/main.py (FastAPI app, CORS, GZip, logging, health check)
- [x] apps/api/requirements.txt
- [x] apps/api/db/__init__.py
- [x] apps/api/db/config.py (Pydantic Settings, lru_cache singleton)
- [x] apps/api/db/database.py (SQLAlchemy engine, retry/backoff, get_db())
- [x] apps/api/db/models.py (ORM models for raw/staging/marts schemas)
- [x] apps/api/routers/__init__.py
- [x] apps/api/routers/executive.py (MRR, ARR, NRR, churn, active accounts)
- [x] apps/api/routers/revenue.py (MRR bridge, waterfall, by plan/region)
- [x] apps/api/routers/cohorts.py (retention heatmaps, NRR by cohort)
- [x] apps/api/routers/health.py (health scores, churn risk, risk flags)
- [x] apps/api/routers/funnel.py (lead→trial→paid conversion analytics)

## Phase 4: Next.js Base Setup ✅
- [x] apps/web/package.json (Next.js 14.2.3, all deps)
- [x] apps/web/tsconfig.json
- [x] apps/web/next.config.js (active config, port 3001)
- [x] apps/web/next.config.ts (stub)
- [x] apps/web/tailwind.config.ts
- [x] apps/web/postcss.config.js
- [x] apps/web/app/globals.css (dark/light theme, CSS variables)
- [x] apps/web/app/layout.tsx (root layout, ThemeProvider)
- [x] apps/web/app/not-found.tsx
- [x] apps/web/types/index.ts (all TypeScript interfaces)
- [x] apps/web/lib/utils.ts (cn helper)
- [x] apps/web/lib/api.ts (API client with mock fallback)
- [x] apps/web/lib/mock-data.ts (complete mock dataset)
- [x] apps/web/lib/formatters.ts (currency, percent, number formatters)
- [x] apps/web/components/ui/button.tsx
- [x] apps/web/components/ui/card.tsx
- [x] apps/web/components/ui/badge.tsx
- [x] apps/web/components/ui/separator.tsx
- [x] apps/web/components/ui/tabs.tsx
- [x] apps/web/components/ui/select.tsx
- [x] apps/web/components/ui/progress.tsx
- [x] apps/web/components/ui/scroll-area.tsx
- [x] apps/web/components/ui/skeleton.tsx
- [x] apps/web/components/providers/ThemeProvider.tsx

## Phase 5: Landing Page ✅
- [x] apps/web/app/page.tsx (main landing page, all 8 sections)
- [x] apps/web/components/landing/Navbar.tsx
- [x] apps/web/components/landing/HeroSection.tsx (particle canvas, floating metrics, dashboard mockup)
- [x] apps/web/components/landing/KPIHighlights.tsx (animated counters, 6 KPI cards)
- [x] apps/web/components/landing/WhyItMatters.tsx
- [x] apps/web/components/landing/FeaturesSection.tsx
- [x] apps/web/components/landing/ArchitectureSection.tsx
- [x] apps/web/components/landing/InsightsSection.tsx
- [x] apps/web/components/landing/CTASection.tsx
- [x] apps/web/components/landing/Footer.tsx
- [x] apps/web/components/landing/SectionWrapper.tsx (Framer Motion scroll reveal)
- [x] apps/web/components/landing/AnimatedCounter.tsx
- [x] apps/web/components/three/AnalyticsSphere.tsx (React Three Fiber 3D sphere)

## Phase 6: Dashboard Pages ✅
- [x] apps/web/app/dashboard/layout.tsx (sidebar + main flex layout)
- [x] apps/web/app/dashboard/page.tsx (Executive Overview: KPIs, MRR trend, waterfall, top accounts)
- [x] apps/web/app/dashboard/revenue/page.tsx (Revenue Movements: bridge, by plan/region, invoice failures)
- [x] apps/web/app/dashboard/cohorts/page.tsx (Cohort Retention: heatmap, NRR, logo churn)
- [x] apps/web/app/dashboard/health/page.tsx (Customer Health: scores, risk quadrant, risky accounts)
- [x] apps/web/app/dashboard/funnel/page.tsx (Funnel & Growth: conversion, by channel, expansion)
- [x] apps/web/app/dashboard/loading.tsx
- [x] apps/web/app/dashboard/error.tsx
- [x] apps/web/app/dashboard/revenue/loading.tsx
- [x] apps/web/app/dashboard/cohorts/loading.tsx
- [x] apps/web/app/dashboard/health/loading.tsx
- [x] apps/web/app/dashboard/funnel/loading.tsx
- [x] apps/web/components/dashboard/KPICard.tsx
- [x] apps/web/components/charts/MRRTrendChart.tsx
- [x] apps/web/components/charts/WaterfallChart.tsx
- [x] apps/web/components/charts/MRRBridgeChart.tsx
- [x] apps/web/components/charts/FunnelChart.tsx (FunnelViz + ConversionByChannelChart)
- [x] apps/web/components/charts/CohortHeatmap.tsx
- [x] apps/web/components/layout/DashboardSidebar.tsx
- [x] apps/web/components/layout/DashboardHeader.tsx

## Phase 7: Polish & Finalization ✅
- [x] Loading skeletons (skeleton.tsx + loading.tsx per route)
- [x] Error boundaries (error.tsx per route)
- [x] 404 page (not-found.tsx)
- [x] Dark/light theme toggle (ThemeProvider + DashboardHeader)
- [x] Responsive design (Tailwind responsive classes throughout)
- [x] TypeScript: ZERO errors (tsc --noEmit verified)
- [x] npm install: 590 packages, no blocking errors
- [x] docker-compose.yml: Complete with all 8 services
- [x] Makefile: Unix/Mac developer experience
- [x] scripts/start-local.ps1: Windows developer experience
- [x] apps/api/routers/__init__.py: Package init
- [x] apps/api/__init__.py: Package init
- [x] vercel.json: Frontend deployment config
- [x] render.yaml: Backend deployment config

## Metrics Implemented ✅
- [x] MRR (Monthly Recurring Revenue)
- [x] ARR = MRR × 12
- [x] New MRR, Expansion MRR, Contraction MRR, Churned MRR, Reactivation MRR
- [x] Net New MRR = New + Expansion + Reactivation - Contraction - Churn
- [x] Logo Churn Rate = Customers Lost / Customers at Start
- [x] Revenue Churn Rate = (MRR Lost from Churn + Contraction) / Starting MRR
- [x] NRR = (Starting MRR + Expansion + Reactivation - Contraction - Churn) / Starting MRR
- [x] GRR = (Starting MRR - Contraction - Churn) / Starting MRR
- [x] ARPA = Total MRR / Active Accounts
- [x] Trial-to-paid conversion rate
- [x] Health score (weighted composite: usage 25%, seat util 20%, feature adoption 15%, support 15%, CSAT 10%, payment 10%, tenure 5%)

## Risk Flags Implemented ✅
- [x] Usage drops >40% month-over-month
- [x] No login in 14 days
- [x] 2+ unresolved high-priority tickets
- [x] Failed payment in current cycle
- [x] CSAT < 3
- [x] Seat utilization below 25%

## Data Model ✅
- [x] accounts (300 synthetic accounts)
- [x] plans (starter $99, growth $299, business $799, enterprise $2499+)
- [x] subscriptions (24 months history)
- [x] invoices (with payment failures)
- [x] product usage events (50K+ events)
- [x] support tickets (3141 tickets)
- [x] leads/opportunities (1200 leads)
- [x] calendar table
- [x] features table
