
---

### **3️⃣ Task List (`SpendSense_Task_List.md`)**

```markdown
# SpendSense Task List

## Phase 1: Data Foundation
- [ ] Generate 50-100 synthetic users with diverse income and spending patterns
- [ ] Simulate accounts: checking, savings, credit card, money market, HSA
- [ ] Simulate liabilities: credit cards, mortgages, student loans
- [ ] Implement payroll simulation: monthly, semi-monthly, biweekly
- [ ] Store in SQLite/Parquet; validate schemas
- [ ] Provide CSV/JSON ingestion interface

## Phase 2: Feature Engineering
- [ ] Partition transactions into 30-day and 180-day discrete windows
- [ ] Compute behavioral signals:
  - Subscriptions
  - Savings
  - Credit
  - Income stability
- [ ] Verify signals against synthetic profiles

## Phase 3: Persona System
- [ ] Implement persona assignment logic for 5 personas
- [ ] Apply prioritization rules for multiple matches
- [ ] Document persona criteria and rationales

## Phase 4: Recommendation Engine
- [ ] Build education content catalog
- [ ] Optionally integrate LLM for dynamic content
- [ ] Build dynamic partner offers with deterministic eligibility logic
- [ ] Generate recommendations with plain-language rationales

## Phase 5: Guardrails & Operator UX
- [ ] Implement consent tracking; revocation takes immediate effect
- [ ] Enforce eligibility and tone checks
- [ ] Build web-based operator dashboard
  - Review signals, persona, recommendations
  - Approve/override functionality
  - Filter by persona, search by user ID
  - Decision trace visibility

## Phase 6: Evaluation & Metrics
- [ ] Build automatic scoring metrics:
  - Coverage
  - Explainability
  - Relevance
  - Latency
  - Fairness
- [ ] Generate JSON/CSV reports and charts/graphs

## Phase 7: API & Deployment
- [ ] Implement REST API for all modules
- [ ] Ensure local-only deployment
- [ ] Decide: single script to run backend + frontend, or separate scripts
- [ ] Write setup instructions and README

## Phase 8: Testing & Documentation
- [ ] Unit and integration tests (≥10)
- [ ] Document schemas, decisions, and AI prompt usage
- [ ] Include "not financial advice" disclaimers
- [ ] Record evaluation results

