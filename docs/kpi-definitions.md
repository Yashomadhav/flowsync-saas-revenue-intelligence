# FlowSync SaaS Revenue Intelligence — KPI Definitions

## Revenue KPIs

### MRR (Monthly Recurring Revenue)
**Definition:** Recurring subscription revenue normalized to monthly value.  
**Formula:** `SUM(monthly_subscription_value)`  
**Used for:** Core growth monitoring, retention analysis, expansion/churn attribution.

### ARR (Annual Recurring Revenue)
**Definition:** Annualized recurring revenue based on MRR.  
**Formula:** `ARR = MRR * 12`  
**Used for:** Executive reporting, valuation narrative, annual planning.

### New MRR
**Definition:** MRR from newly converted paying accounts in period.  
**Used for:** Top-of-funnel quality and GTM effectiveness.

### Expansion MRR
**Definition:** Additional MRR from existing accounts via upgrades, seat growth, add-ons.  
**Used for:** Upsell/cross-sell performance and product-led expansion strategy.

### Contraction MRR
**Definition:** MRR reduction from downgrades, seat decreases, discounting.  
**Used for:** Revenue risk and commercial quality signal.

### Churned MRR
**Definition:** MRR lost from account cancellations.  
**Used for:** Revenue attrition and retention strategy prioritization.

### Reactivation MRR
**Definition:** MRR regained from previously churned customers returning.  
**Used for:** Win-back program performance.

### Net New MRR
**Definition:** Net monthly MRR movement after all additions/losses.  
**Formula:** `Net New MRR = New + Expansion + Reactivation - Contraction - Churn`  
**Used for:** True momentum of recurring revenue engine.

---

## Retention & Churn KPIs

### Logo Churn Rate
**Definition:** Share of customers lost in period.  
**Formula:** `Customers Lost During Period / Customers At Start Of Period`  
**Used for:** Customer retention quality independent of account size.

### Revenue Churn Rate
**Definition:** Share of starting MRR lost due to churn and contraction.  
**Formula:** `(Churned MRR + Contraction MRR) / Starting MRR`  
**Used for:** Economic retention signal.

### NRR (Net Revenue Retention)
**Definition:** Retained and expanded revenue from opening customer base.  
**Formula:** `(Starting MRR + Expansion + Reactivation - Contraction - Churn) / Starting MRR`  
**Interpretation:**  
- `>100%` = expansion outpaces losses  
- `<100%` = net contraction of retained base

### GRR (Gross Revenue Retention)
**Definition:** Revenue retained excluding expansion/reactivation upside.  
**Formula:** `(Starting MRR - Contraction - Churn) / Starting MRR`  
**Used for:** Baseline retention health of current book.

### ARPA / ARPU
**Definition:** Average recurring revenue per active account/user.  
**Formula:** `Total MRR / Active Accounts`  
**Used for:** Pricing, packaging, and segment monetization strategy.

---

## Funnel & Growth KPIs

### Lead to Trial Conversion Rate
**Definition:** Share of leads that start trial.  
**Formula:** `Trial Starts / Total Leads`

### Trial to Paid Conversion Rate
**Definition:** Share of trial users converting to paid.  
**Formula:** `Paid Conversions / Trial Starts`

### Overall Conversion Rate
**Definition:** End-to-end conversion from lead to paid.  
**Formula:** `Paid Conversions / Total Leads`

### Sales Cycle Duration
**Definition:** Average days from lead creation to paid conversion.  
**Used for:** Pipeline velocity, forecast confidence, channel quality.

---

## Customer Health KPIs

### Health Score (0–100)
**Definition:** Composite risk/health metric at account-month grain.

**Default weighting model:**
- Usage Frequency: 25%
- Active Users vs Seats (Seat Utilization): 20%
- Feature Adoption Breadth: 15%
- Support Burden: 15%
- CSAT: 10%
- Payment Reliability: 10%
- Tenure Stability: 5%

### Risk Flags
Flagged when any condition below is true:
- Usage drops > 40% month-over-month
- No login in 14 days
- 2+ unresolved high-priority tickets
- Failed payment in current cycle
- CSAT < 3
- Seat utilization < 25%

---

## Segment/Diagnostic KPIs

### Revenue by Plan / Region / Industry / Size
**Definition:** MRR distribution across key slices.  
**Used for:** GTM allocation and ICP fit analysis.

### Cohort Retention (Customer / Revenue)
**Definition:** Retention trajectory by acquisition cohort over time.  
**Used for:** Onboarding effectiveness and payback quality by cohort.

### Support Burden
**Definition:** Ticket volume/severity/response outcomes by account.  
**Used for:** Churn prevention and CS operation prioritization.
