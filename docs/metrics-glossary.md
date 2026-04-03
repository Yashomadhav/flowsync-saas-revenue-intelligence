# FlowSync Revenue Intelligence — Metrics Glossary

## Core Revenue Metrics

### MRR (Monthly Recurring Revenue)
**Definition**: The normalized monthly value of all active recurring subscriptions.  
**Formula**: `SUM(subscription_amount / billing_period_months)` for all active subscriptions  
**Example**: A $1,200/year subscription contributes $100/month to MRR  
**Why it matters**: The single most important SaaS health metric. Tracks predictable revenue.

---

### ARR (Annual Recurring Revenue)
**Definition**: Annualized version of MRR.  
**Formula**: `MRR × 12`  
**Example**: $500K MRR → $6M ARR  
**Why it matters**: Used for valuation, investor reporting, and annual planning.

---

### New MRR
**Definition**: MRR added from brand-new customers who had no prior subscription.  
**Formula**: `SUM(first_month_mrr)` for accounts with `movement_type = 'new'`  
**Example**: 10 new customers at $500/month average = $5,000 New MRR  
**Why it matters**: Measures sales team effectiveness and top-of-funnel health.

---

### Expansion MRR
**Definition**: MRR increase from existing customers (upgrades, seat additions, add-ons).  
**Formula**: `SUM(current_mrr - previous_mrr)` where `current_mrr > previous_mrr` and account was active last month  
**Example**: Customer upgrades from $500 to $800/month → $300 Expansion MRR  
**Why it matters**: Expansion is the most efficient revenue growth — no CAC required.

---

### Contraction MRR
**Definition**: MRR decrease from existing customers (downgrades, seat reductions).  
**Formula**: `SUM(previous_mrr - current_mrr)` where `current_mrr < previous_mrr` and account still active  
**Example**: Customer downgrades from $800 to $500/month → $300 Contraction MRR  
**Why it matters**: Signals dissatisfaction or budget pressure before full churn.

---

### Churned MRR
**Definition**: MRR lost from customers who cancelled their subscription entirely.  
**Formula**: `SUM(last_month_mrr)` for accounts with `movement_type = 'churn'`  
**Example**: 5 customers cancel at $400/month average = $2,000 Churned MRR  
**Why it matters**: Direct revenue loss. High churn destroys growth even with strong new sales.

---

### Reactivation MRR
**Definition**: MRR from previously churned customers who re-subscribed.  
**Formula**: `SUM(current_mrr)` for accounts with `movement_type = 'reactivation'`  
**Example**: Former customer returns at $600/month = $600 Reactivation MRR  
**Why it matters**: Indicates product-market fit recovery and win-back program effectiveness.

---

### Net New MRR
**Definition**: The net change in MRR for a given period.  
**Formula**: `New MRR + Expansion MRR + Reactivation MRR - Contraction MRR - Churned MRR`  
**Example**: $10K New + $3K Expansion + $1K Reactivation - $2K Contraction - $4K Churn = $8K Net New MRR  
**Why it matters**: The "bottom line" of revenue growth. Positive = growing, negative = shrinking.

---

## Churn Metrics

### Logo Churn Rate
**Definition**: Percentage of customers lost in a period.  
**Formula**: `Customers Lost During Period / Customers at Start of Period × 100`  
**Example**: 5 churned / 100 starting = 5% Logo Churn  
**Benchmark**: World-class SaaS < 2% monthly, < 5% annually  
**Why it matters**: Measures customer retention independent of revenue size.

---

### Revenue Churn Rate
**Definition**: Percentage of MRR lost from churn and contraction.  
**Formula**: `(Churned MRR + Contraction MRR) / Starting MRR × 100`  
**Example**: ($4K Churn + $2K Contraction) / $100K Starting MRR = 6% Revenue Churn  
**Benchmark**: World-class SaaS < 1% monthly  
**Why it matters**: More nuanced than logo churn — accounts for revenue size of churned customers.

---

### NRR (Net Revenue Retention)
**Definition**: Percentage of revenue retained from existing customers including expansion.  
**Formula**: `(Starting MRR + Expansion MRR + Reactivation MRR - Contraction MRR - Churned MRR) / Starting MRR × 100`  
**Example**: ($100K + $15K + $2K - $3K - $5K) / $100K = 109% NRR  
**Benchmark**: Elite SaaS > 120%, Good > 100%, Concerning < 90%  
**Why it matters**: NRR > 100% means revenue grows even without new customers. The holy grail.

---

### GRR (Gross Revenue Retention)
**Definition**: Percentage of revenue retained excluding expansion (floor metric).  
**Formula**: `(Starting MRR - Contraction MRR - Churned MRR) / Starting MRR × 100`  
**Example**: ($100K - $3K - $5K) / $100K = 92% GRR  
**Benchmark**: Elite SaaS > 95%, Good > 85%  
**Why it matters**: Shows the "floor" of retention — how much you keep before any upsell.  
**Note**: GRR is always ≤ 100% (expansion is excluded by definition).

---

## Efficiency Metrics

### ARPA (Average Revenue Per Account)
**Definition**: Average MRR per active account.  
**Formula**: `Total MRR / Number of Active Accounts`  
**Example**: $500K MRR / 1,000 accounts = $500 ARPA  
**Why it matters**: Tracks monetization efficiency. Rising ARPA = successful upsell motion.

---

### ARPU (Average Revenue Per User)
**Definition**: Average MRR per active user (seat-level).  
**Formula**: `Total MRR / Total Active Users`  
**Example**: $500K MRR / 5,000 users = $100 ARPU  
**Why it matters**: Useful for seat-based pricing models.

---

### Trial-to-Paid Conversion Rate
**Definition**: Percentage of trial accounts that convert to paid subscriptions.  
**Formula**: `Paid Conversions / Trial Starts × 100`  
**Example**: 50 paid / 200 trials = 25% conversion  
**Benchmark**: B2B SaaS typically 15-25%  
**Why it matters**: Key indicator of product-market fit and onboarding effectiveness.

---

## Health Score Components

### Account Health Score (0–100)

| Component | Weight | Scoring Logic |
|-----------|--------|---------------|
| Usage Frequency | 25% | Daily active sessions vs expected |
| Seat Utilization | 20% | Active users / licensed seats |
| Feature Adoption | 15% | Features used / features available |
| Support Burden | 15% | Inverse of open high-priority tickets |
| CSAT Score | 10% | Normalized 1-5 CSAT to 0-100 |
| Payment Reliability | 10% | Inverse of payment failures |
| Tenure Stability | 5% | Months as customer (capped at 24) |

**Score Bands**:
- 🟢 **Healthy**: 75–100
- 🟡 **At Risk**: 50–74
- 🔴 **Critical**: 0–49

---

### Risk Flags

| Flag | Trigger | Severity |
|------|---------|----------|
| Usage Drop | >40% MoM decline in sessions | 🔴 Critical |
| Login Inactivity | No login in 14+ days | 🔴 Critical |
| Support Overload | 2+ unresolved high-priority tickets | 🔴 Critical |
| Payment Failure | Failed payment in current billing cycle | 🔴 Critical |
| Low CSAT | CSAT score < 3.0 | 🔴 Critical |
| Low Seat Utilization | Active users < 25% of licensed seats | 🟡 Warning |
| Feature Stagnation | No new features adopted in 60 days | 🟡 Warning |
| Downgrade Signal | Contraction MRR in last 2 months | 🟡 Warning |

---

## Cohort Analysis

### Customer Cohort
**Definition**: Group of customers who started in the same calendar month.  
**Retention at Month N**: `Customers from cohort still active at month N / Cohort starting size × 100`

### Revenue Cohort
**Definition**: Revenue-weighted cohort analysis.  
**Revenue Retention at Month N**: `MRR from cohort at month N / Starting MRR of cohort × 100`  
**Note**: Revenue retention can exceed 100% due to expansion MRR.

---

## Funnel Metrics

### Lead-to-Trial Rate
**Formula**: `Trial Starts / Total Leads × 100`

### Trial-to-Paid Rate
**Formula**: `Paid Conversions / Trial Starts × 100`

### Lead-to-Paid Rate (Overall)
**Formula**: `Paid Conversions / Total Leads × 100`

### Sales Cycle Duration
**Formula**: `AVG(paid_date - lead_created_date)` in days

### Time-to-Value (TTV)
**Formula**: `AVG(first_meaningful_action_date - trial_start_date)` in days

---

## Segment Definitions

### Company Size
| Segment | Employee Count |
|---------|---------------|
| SMB | 1–50 |
| Mid-Market | 51–500 |
| Enterprise | 501+ |

### Plan Tiers
| Plan | Monthly Price | Features |
|------|--------------|---------|
| Starter | $99 | 5 users, basic workflows |
| Growth | $299 | 25 users, advanced automation |
| Business | $799 | 100 users, analytics, API |
| Enterprise | $2,499+ | Unlimited, SSO, SLA |

### Acquisition Channels
- **Organic Search** — SEO-driven inbound
- **Paid Search** — Google/Bing ads
- **Content/Blog** — Content marketing
- **Referral** — Customer referrals
- **Partner** — Channel partners
- **Direct/Outbound** — Sales-led outreach
- **Product-Led** — Freemium/viral
