# SpendSense PRD

## Project Overview
SpendSense transforms Plaid-style banking transaction data into explainable, consent-aware behavioral insights and personalized financial education. The system detects patterns, assigns personas, and delivers recommendations with clear rationales.

### Goals
- Explainable behavioral signal detection
- Persona assignment (5 personas)
- Personalized financial education
- Dynamic partner offers
- Consent, eligibility, and tone guardrails
- Operator oversight and evaluation

### Scope
- Local-only deployment
- Synthetic dataset (50-100 users)
- Modular, rules-based baseline; optional LLM enhancements
- REST API + web-based operator dashboard

## Features

### 1. Data Layer
- **Synthetic data generation**:
  - 50-100 users, diverse income and account types
  - Transactions, accounts, and liabilities
  - Realistic payroll simulation: monthly, semi-monthly, biweekly
- **Storage**:
  - SQLite for relational data
  - Parquet for analytics
  - JSON for configs/logs

### 2. Behavioral Signal Detection
- Time windows: **30-day** and **180-day** discrete non-overlapping windows
- Signals:
  - **Subscriptions:** recurring spend, share of total spend
  - **Savings:** net inflow, growth rate, emergency fund coverage
  - **Credit:** utilization, overdue, interest, minimum payment only
  - **Income Stability:** payroll detection, frequency variability, cash-flow buffer

### 3. Persona Assignment
- **Persona 1:** High Utilization
- **Persona 2:** Variable Income Budgeter
- **Persona 3:** Subscription-Heavy
- **Persona 4:** Savings Builder
- **Persona 5:** Frugal Planner
  - Criteria: consistently low discretionary spend, maintains savings, avoids high-risk products
  - Primary Focus: disciplined budgeting, frugal planning, emergency fund growth
- Single **primary persona** per user; prioritization rules defined

### 4. Recommendations
- **Education content**:
  - Catalog of pre-written items
  - Optional LLM-generated content for dynamic supplementation
- **Dynamic partner offers**:
  - Fully deterministic based on synthetic profile
  - Eligibility filters simulate realistic constraints
- Output includes plain-language rationale citing specific data points

### 5. Guardrails
- Consent must be explicit; revocation immediately takes effect
- Eligibility and tone checks enforced
- Disclosure: "This is educational content, not financial advice."

### 6. Operator View
- Web-based dashboard
- Review signals, persona, and recommendations
- Approve/override recommendations
- Filter by persona, search by user ID
- Decision trace and rationale visibility

### 7. Evaluation & Metrics
- Automatic scoring of:
  - Coverage: persona + ≥3 behaviors
  - Explainability: rationale included
  - Relevance: rules-based evaluation
  - Latency <5 seconds per user
  - Fairness: based on synthetic data characteristics
- Output charts, JSON/CSV reports

### Technology Stack
- Python-based backend
- REST API
- Web-based dashboard (frontend)
- Local storage only
- Optional LLM integration

### Phased Build Strategy
1. **Data Foundation:** Generate and validate synthetic dataset
2. **Feature Engineering:** Compute behavioral signals
3. **Persona System:** Assign primary persona
4. **Recommendations:** Generate education content + partner offers
5. **Guardrails & UX:** Consent, eligibility, tone; operator dashboard
6. **Evaluation:** Metrics, reporting, and visualization

### Success Criteria
- 100% coverage, explainability, auditability
- Recommendations generated within <5 seconds
- ≥10 unit/integration tests passing
- Complete documentation of schemas, decision logs, AI prompts
