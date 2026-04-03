# FlowSync SaaS Revenue Intelligence — Architecture

## 1) System Architecture (Mermaid)

```mermaid
flowchart LR
    A[Data Generators<br/>Python synthetic SaaS data] --> B[(PostgreSQL raw schema)]
    B --> C[dbt staging models<br/>type cleanup + conformance]
    C --> D[dbt marts models<br/>facts + business marts]

    D --> E[FastAPI service<br/>/api/v1 endpoints]
    E --> F[Next.js Web App<br/>Dashboards + Landing]
    F --> U[Business Users / Hiring Reviewers]

    subgraph Infra
      G[Docker Compose]
      H[Vercel Frontend]
      I[Render/Railway API]
      J[Managed PostgreSQL]
      K[GitHub Actions<br/>CI + dbt run/test]
    end

    E -.deploy.-> I
    F -.deploy.-> H
    D -.hosted on.-> J
    K -.automates.-> C
    K -.automates.-> D
```

---

## 2) Data Flow Diagram (Mermaid)

```mermaid
flowchart TD
    S1[Generate Accounts/Plans/Subscriptions]
    S2[Generate Invoices/Usage/Tickets/Leads]
    S3[CSV Outputs]

    S1 --> S3
    S2 --> S3

    S3 --> R1[Ingest Pipeline<br/>scripts/ingest/ingest_pipeline.py]
    R1 --> R2[(raw.* tables)]

    R2 --> T1[dbt staging<br/>stg_accounts, stg_subscriptions, ...]
    T1 --> T2[dbt marts<br/>fct_mrr_movements, fct_account_monthly_health,<br/>fct_customer_cohorts, fct_sales_conversion,<br/>mart_exec_revenue_summary, mart_customer_success_summary]

    T2 --> API[FastAPI Routers]
    API --> WEB[Next.js Dashboards]

    T2 --> INSIGHTS[Business Insights Layer<br/>MRR, NRR, churn, health, funnel]
```

---

## 3) Architectural Explanation

### Frontend
- **Framework:** Next.js (App Router) + TypeScript
- **UI:** Tailwind + reusable UI components
- **Charts:** Recharts for KPI trend and segment analysis
- **Interaction model:** Multi-page analytics UI with fallback mock data if API unavailable

### Backend
- **Framework:** FastAPI
- **Access pattern:** Router-based domain endpoints (`executive`, `revenue`, `cohorts`, `health`, `funnel`)
- **Data retrieval:** SQL-backed endpoint responses from marts tables

### Data Platform
- **Warehouse:** PostgreSQL
- **Modeling style:** Medallion (raw → staging → marts)
- **Transformation layer:** dbt
- **Synthetic data:** Python generators for realistic SaaS lifecycle behavior

### DevOps / Deployment
- **Local orchestration:** Docker Compose (`postgres`, `api`, `web`, optional `dbt`)
- **CI/CD:** GitHub Actions for lint/test and dbt run/test scheduling
- **Runtime targets:**
  - Frontend → Vercel
  - API + Postgres → Render or Railway managed services

---

## 4) Design Rationale

1. **Separation of concerns**
   - Data modeling logic in dbt
   - API logic in FastAPI
   - Presentation logic in Next.js

2. **Portfolio realism**
   - SaaS metrics mirror real RevOps/CSOps reporting needs
   - Cohorts + health + funnel provide multi-functional business lens

3. **Deployability**
   - Local-first Docker workflow and cloud-ready platform mapping
   - CI-compatible dbt execution model

4. **Extensibility**
   - Additional entities and KPIs can be added via staging + marts without major API/UI rewrites
