# FlowSync SaaS Revenue Intelligence Dashboard

Production-grade full-stack BI platform for a fictional B2B SaaS company (**FlowSync**) that demonstrates revenue analytics, customer health intelligence, cohort retention analysis, and funnel performance in an enterprise-ready architecture.

---

## 1) Business Problem Statement

B2B SaaS leaders need one place to understand:
- whether recurring revenue is actually growing sustainably,
- which movements (new/expansion/contraction/churn/reactivation) drive change,
- which cohorts and customer segments retain best,
- which accounts are at churn risk before renewal loss happens,
- and how GTM funnel quality translates to long-term revenue value.

Traditional dashboards are fragmented across finance, product, support, and sales tooling.  
FlowSync Revenue Intelligence unifies these views into a single decision layer.

---

## 2) Project Overview

This project is a portfolio-grade end-to-end BI stack including:

- **Modern frontend:** Next.js + TypeScript + Tailwind + shadcn/ui + Recharts
- **Analytics API:** FastAPI service exposing dashboard-ready endpoints
- **Warehouse foundation:** PostgreSQL with medallion-style modeling
- **Transformation layer:** dbt models for business metrics and marts
- **Synthetic data engine:** realistic SaaS data generation and ingestion
- **Deployment path:** Vercel (frontend), Render/Railway (API + DB), GitHub Actions (CI/dbt)

Primary business domains:
1. Executive Overview  
2. Revenue Movements  
3. Cohort Retention  
4. Customer Health & Churn Risk  
5. Funnel & Growth

---

## 3) Architecture Explanation

See detailed architecture in: [`docs/architecture.md`](docs/architecture.md)

### High-level layers
- **Presentation:** Next.js dashboard and landing experience
- **API:** FastAPI `/api/v1/*` endpoints
- **Analytics data:** marts/facts in PostgreSQL
- **Transformation:** dbt from raw → staging → marts
- **Ingestion:** Python generators + ingestion scripts

---

## 4) Data Model Explanation

### Medallion approach
- **Raw (`raw.*`)**: source-like ingestion tables
- **Staging (`staging.*`)**: typed, cleaned, conformed entities
- **Marts (`marts.*`)**: metric-ready facts and summaries

Core entities include:
- accounts
- plans
- subscriptions
- invoices
- usage events
- support tickets
- leads/opportunities
- calendar/features (model-supporting dimensions)

Detailed data dictionary: [`docs/data-dictionary.md`](docs/data-dictionary.md)

---

## 5) KPI Definitions

Primary KPI formulas and interpretation are documented in:
- [`docs/kpi-definitions.md`](docs/kpi-definitions.md)

Key metrics:
- MRR / ARR
- New / Expansion / Contraction / Churn / Reactivation MRR
- Net New MRR
- Logo Churn / Revenue Churn
- NRR / GRR
- ARPA
- Lead→Trial→Paid conversion
- Health score and risk flag framework

---

## 6) Dashboard Page Descriptions

### Executive Overview (`/dashboard`)
- Top-line KPIs: MRR, ARR, NRR, churn, active accounts
- MRR trend and revenue waterfall
- Revenue by plan/region
- Top expansion and top churn-risk account lists

### Revenue Movements (`/dashboard/revenue`)
- MRR bridge by month
- Account-level movement analysis
- New MRR by acquisition channel
- Invoice/payment failure trends

### Cohort Retention (`/dashboard/cohorts`)
- Customer retention cohort heatmap
- Revenue retention (NRR) cohort heatmap
- Churn trend and segment retention comparisons

### Customer Health & Churn Risk (`/dashboard/health`)
- Health score distribution
- Risk quadrant (usage vs health)
- Risk flags and support burden tables

### Funnel & Growth (`/dashboard/funnel`)
- Lead→Trial→Paid funnel
- Conversion by channel
- Sales cycle trends
- Expansion by segment

---

## 7) Setup Instructions (Local)

### Prerequisites
- Docker + Docker Compose
- Node.js 18+
- Python 3.10+ (if running scripts outside containers)

### Quick start
```bash
# from project root
docker-compose up --build
```

Optional profiles:
```bash
docker-compose --profile tools up -d      # pgAdmin
docker-compose --profile dbt up -d        # dbt container
docker-compose --profile seed up          # one-shot seed
docker-compose --profile ingest up        # ingest + validate
```

Service URLs (default):
- Web: http://localhost:3000
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- pgAdmin (tools profile): http://localhost:5050

### Common commands
Use `Makefile` (Unix/Mac) and `scripts/start-local.ps1` (Windows) for convenience tasks:
- generate-data
- load-data
- run-dbt
- run-app stack orchestration

---

## 8) Deployment Instructions

### Frontend → Vercel
- Deploy `apps/web`
- Configure `NEXT_PUBLIC_API_URL` to deployed API base
- Optionally set `NEXT_PUBLIC_USE_MOCK_DATA=false`

### API → Render or Railway
- Deploy `apps/api`
- Set `DATABASE_URL`, `API_PREFIX`, `ALLOWED_ORIGINS`, `SECRET_KEY`
- Health endpoint should be mapped to `/health`

### PostgreSQL → Managed DB (Render/Railway)
- Provision managed PostgreSQL
- Apply schema/migrations
- Run ingestion/seed for demo data
- Trigger dbt run/test job

### dbt orchestration
- Run via GitHub Actions workflow (`.github/workflows/dbt-run.yml`)
- Optional scheduled refresh using cron-based workflow triggers

Existing deployment config files:
- `vercel.json`
- `render.yaml`

---

## 9) Sample Insights (from modeled analytics)

1. **Enterprise accounts show highest ARPA but slower conversion**
   - Larger contracts increase value per account, but sales cycles are longer.

2. **Low feature adoption in first 30 days correlates with churn risk**
   - Early product engagement is a strong leading indicator.

3. **Expansion MRR is concentrated in Growth/Pro-like mid-market tiers**
   - These segments tend to show the best upsell elasticity.

4. **High support escalations correlate with lower retention**
   - Ticket severity/load acts as an early warning for account deterioration.

5. **Some channels produce high volume but lower quality**
   - Funnel conversion and first-month MRR differ meaningfully across channels.

---

## 10) Future Improvements

- Add row-level security and full auth/tenant isolation
- Add SLA-monitoring and anomaly detection alerts
- Integrate real event streams (Kafka/PubSub) for near real-time updates
- Introduce ML churn propensity scoring alongside rule-based health score
- Expand account drill-through experience with comparative benchmarking
- Add budget/forecast scenario simulation

---

## 11) Folder Structure Explanation

```text
saas-revenue-intelligence/
├── apps/
│   ├── web/                    # Next.js frontend
│   └── api/                    # FastAPI backend
├── data/generators/            # Synthetic SaaS data generation
├── dbt_project/                # dbt models & configs
├── database/migrations/        # SQL schema/migration files
├── docker/                     # Dockerfiles and DB init assets
├── docs/                       # Architecture, KPIs, dictionary, API docs
├── scripts/                    # Ingestion/validation/startup automation
├── .github/workflows/          # CI/CD and dbt jobs
├── docker-compose.yml          # Local stack orchestration
└── README.md
```

---

## 12) Screenshots Placeholders

Add final demo captures to:
- `docs/assets/landing-page.png`
- `docs/assets/executive-overview.png`
- `docs/assets/revenue-movements.png`
- `docs/assets/cohort-retention.png`
- `docs/assets/health-risk.png`
- `docs/assets/funnel-growth.png`

Then reference them in this README for portfolio publication.

---

## 13) Interview-Ready Project Summary

**What this demonstrates**
- Full-stack BI system design from data generation to decision UX
- SaaS finance metric rigor (MRR, NRR, GRR, churn decomposition)
- Practical data engineering (warehouse modeling + dbt transformations)
- Production-minded API design and deployment strategy
- Strong analytics storytelling through dashboard UX

**How to pitch in interviews (30–45 sec)**
> “I built a full-stack SaaS Revenue Intelligence platform for a fictional B2B company. It models end-to-end recurring revenue, cohorts, customer health, and funnel performance using PostgreSQL + dbt marts, serves analytics through FastAPI, and presents executive-grade dashboards in Next.js. The project is deployable with Docker and cloud targets (Vercel + Render/Railway), and includes CI workflows for dbt and app validation.”

---

## 14) Documentation Index

- Architecture + diagrams: [`docs/architecture.md`](docs/architecture.md)
- KPI definitions: [`docs/kpi-definitions.md`](docs/kpi-definitions.md)
- Data dictionary: [`docs/data-dictionary.md`](docs/data-dictionary.md)
- API overview: [`docs/api-overview.md`](docs/api-overview.md)

---

## Tech Stack Snapshot

- **Frontend:** Next.js App Router, TypeScript, Tailwind, Recharts, Framer Motion, React Three Fiber
- **Backend:** FastAPI, SQLAlchemy
- **Data:** PostgreSQL + dbt (medallion)
- **Ops:** Docker Compose, GitHub Actions
- **Deploy:** Vercel + Render/Railway

---

## License

MIT (portfolio/demo use).  
All business entities and datasets are synthetic.
