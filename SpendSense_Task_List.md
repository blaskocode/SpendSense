# SpendSense Task List

## Phase 1: Data Foundation
- [ ] Design and document database schemas (SQLite + Parquet)
- [ ] Create synthetic data generator with realistic variability:
  - [ ] Generate 50-100 users with diverse income levels
  - [ ] Simulate accounts: checking, savings, credit card, money market, HSA
  - [ ] Simulate liabilities: credit cards (APR, min payment), mortgages, student loans
  - [ ] Add subscription jitter (±1-2 days), cancellations (10%), price changes (5%)
  - [ ] Add seasonal patterns: holiday spending, tax refunds, back-to-school
  - [ ] Add life events: job changes (5%), major purchases (3%), medical expenses (10%)
  - [ ] Include edge cases: overdrafts, refunds, chargebacks, pending transactions
- [ ] Implement payroll simulation: monthly, semi-monthly, biweekly with variability
- [ ] Store data in SQLite (relational) and Parquet (analytics)
- [ ] Provide CSV/JSON ingestion interface
- [ ] Validate all schemas and data integrity
- [ ] Use deterministic seeds for reproducibility

## Phase 2: Feature Engineering
- [ ] Build time window partitioner:
  - [ ] Implement 30-day rolling window: [today-30, today-1]
  - [ ] Implement 180-day rolling window: [today-180, today-1]
  - [ ] Windows recalculate daily at midnight UTC
  - [ ] Exclude pending transactions from analysis
  - [ ] Handle edge cases: transactions on window boundaries
- [ ] Implement graceful degradation for new users:
  - [ ] <7 days: "Welcome" persona, basic education only
  - [ ] 7-29 days: Preliminary insights with disclaimer
  - [ ] 30+ days: Full 30-day window analysis
  - [ ] 180+ days: Add long-term window analysis
- [ ] Compute behavioral signals per window:
  - [ ] **Subscriptions:** recurring merchants (≥3 in 90 days), monthly spend, share of total
  - [ ] **Savings:** net inflow, growth rate, emergency fund coverage
  - [ ] **Credit:** utilization (balance/limit), flags for ≥30%, ≥50%, ≥80%
  - [ ] **Credit:** minimum-payment-only detection, interest charges, overdue status
  - [ ] **Income Stability:** payroll ACH detection, frequency, variability, cash-flow buffer
- [ ] Implement signal caching with 24-hour TTL
- [ ] Verify signals against synthetic user profiles
- [ ] Unit test each signal computation

## Phase 3: Persona System
- [ ] Implement 5 personas with clear criteria:
  - [ ] **Priority 1 - High Utilization:** utilization ≥50% OR interest > 0 OR min-payment-only OR overdue
  - [ ] **Priority 2 - Variable Income:** pay gap >45d AND cash buffer <1 month
  - [ ] **Priority 3 - Credit Builder:** no credit OR $0 balance 180+ days AND has checking/savings
  - [ ] **Priority 4 - Subscription-Heavy:** recurring ≥3 AND (monthly spend ≥$50 OR share ≥10%)
  - [ ] **Priority 5 - Savings Builder:** growth ≥2% OR inflow ≥$200/mo AND utilization <30%
- [ ] Implement prioritization logic:
  - [ ] Apply priority order (1 = most urgent)
  - [ ] Tie-breaker: calculate signal strength (sum of normalized signals)
  - [ ] If still tied: use defined order (High Util → Var Income → Credit → Sub → Savings)
- [ ] Assign single primary persona per user
- [ ] Log all matching personas in decision trace
- [ ] Document persona criteria and rationale in `/docs/persona_criteria.md`
- [ ] Unit test persona assignment and edge cases

## Phase 4: Recommendation Engine
- [ ] Build education content catalog with 5 items per persona:
  - [ ] High Utilization: debt paydown, credit score, autopay, balance transfer, timeline
  - [ ] Variable Income: percent budgeting, emergency fund, smoothing, priority spending, forecasting
  - [ ] Credit Builder: credit 101, secured cards, building without debt, myths, credit vs debit
  - [ ] Subscription-Heavy: audit checklist, negotiation, alerts, free alternatives, annual vs monthly
  - [ ] Savings Builder: SMART goals, automation, HYSA, CD laddering, emergency vs investment
- [ ] Build dynamic partner offers with eligibility logic:
  - [ ] Balance transfer cards (if utilization ≥30%, credit proxy ≥650)
  - [ ] HYSA (if building emergency fund, no existing HYSA)
  - [ ] Budgeting apps (if variable income, no linked app)
  - [ ] Subscription tools (if ≥5 subscriptions)
  - [ ] Secured cards (if credit invisible, checking balance ≥$500)
- [ ] Implement rationale generator:
  - [ ] Plain-language "because" statements citing specific data
  - [ ] Example: "Your Visa ending in 4523 is at 68% utilization..."
- [ ] Optional: Integrate LLM for dynamic content generation
  - [ ] Fallback to static catalog if LLM unavailable
  - [ ] Document all prompts in `/docs/ai_prompts.md`
- [ ] Generate 3-5 education items + 1-3 offers per user
- [ ] Unit test recommendation logic and rationale format

## Phase 5: Guardrails & User UX
- [ ] Implement consent tracking:
  - [ ] Create `consent_status` table
  - [ ] Require explicit opt-in before processing
  - [ ] Allow revocation (immediate effect)
  - [ ] Block all recommendations without active consent
- [ ] Implement eligibility checks:
  - [ ] Don't recommend products user already has
  - [ ] Check minimum income/credit requirements
  - [ ] Filter harmful products (no payday loans)
- [ ] Implement tone validator:
  - [ ] Blocklist of shaming phrases ("you're overspending", "bad choices")
  - [ ] Automated tone check before display
  - [ ] Empowering, educational language only
- [ ] Inject disclosure on every recommendation:
  - [ ] "This is educational content, not financial advice..."
- [ ] Build user-facing web dashboard:
  - [ ] Header with persona and welcome message
  - [ ] Insights card (top 3 behavioral signals)
  - [ ] Your Plan: 3-5 education items with rationales
  - [ ] Partner Offers: 1-3 offers with eligibility badges
  - [ ] Data freshness timestamp and disclaimers
  - [ ] Link to consent management
- [ ] Implement feedback system:
  - [ ] Thumbs up/down buttons on each recommendation
  - [ ] "This helped me" / "Not relevant" / "I applied this" / "Already doing this"
  - [ ] Optional free-text feedback (<200 chars)
  - [ ] Store feedback in `feedback` table
- [ ] Unit test guardrails enforcement

## Phase 6: Operator Dashboard
- [ ] Build web-based operator interface:
  - [ ] **User Review:**
    - [ ] Search by user ID
    - [ ] Filter by persona
    - [ ] View 30d and 180d signals
    - [ ] See primary persona + all matching personas
    - [ ] Review recommendations with rationales
    - [ ] Decision trace visibility
  - [ ] **Approval Queue:**
    - [ ] List pending recommendations
    - [ ] Approve or override functionality
    - [ ] Bulk actions: approve all for persona, approve selected
    - [ ] Flag for manual review
    - [ ] Add operator notes
  - [ ] **Analytics View:**
    - [ ] Persona distribution chart
    - [ ] Signal detection rates
    - [ ] Recommendation generation metrics
    - [ ] User engagement rates (from feedback)
    - [ ] Coverage and explainability dashboards
  - [ ] **Feedback Review:**
    - [ ] Aggregate thumbs up/down by recommendation type
    - [ ] Filter by persona or content category
    - [ ] Identify low-performing content
    - [ ] Track "I applied this" action rates
  - [ ] **System Health:**
    - [ ] Latency monitoring
    - [ ] Error logs and data quality alerts
    - [ ] Consent status overview
- [ ] Implement basic authentication for operator access
- [ ] Audit log all operator actions
- [ ] Integration test operator workflows

## Phase 7: Evaluation & Metrics
- [ ] Build automatic scoring system:
  - [ ] **Coverage:** % users with persona + ≥3 behaviors (target: 100%)
  - [ ] **Explainability:** % recommendations with rationales (target: 100%)
  - [ ] **Latency:** time per user (target: <5 seconds)
  - [ ] **Auditability:** % with decision traces (target: 100%)
- [ ] Compute user satisfaction metrics (from feedback):
  - [ ] Engagement Rate: % recommendations interacted with
  - [ ] Helpfulness Score: thumbs up / (up + down)
  - [ ] Action Rate: % marked "I applied this"
- [ ] Build fairness analysis (behavior-based, no demographics):
  - [ ] Detect income quartiles from payroll amounts
  - [ ] Persona distribution across income levels
  - [ ] Average recommendation count by income
  - [ ] Offer eligibility rates by account complexity
  - [ ] Tone sentiment analysis across personas
  - [ ] Flag systematic bias (e.g., low-income excluded)
- [ ] Generate outputs:
  - [ ] JSON/CSV metrics files
  - [ ] Charts and graphs (persona distribution, engagement trends)
  - [ ] 1-2 page summary report
  - [ ] Per-user decision traces
  - [ ] Fairness analysis report
- [ ] Document limitations in `/docs/limitations.md`
- [ ] Integration test evaluation pipeline

## Phase 8: API & Deployment
- [ ] Implement REST API endpoints:
  - [ ] **User Management:**
    - [ ] `POST /users` - Create user
    - [ ] `POST /consent` - Record consent
    - [ ] `DELETE /consent/{user_id}` - Revoke consent
    - [ ] `GET /consent/{user_id}` - Check consent status
  - [ ] **Data & Analysis:**
    - [ ] `GET /profile/{user_id}` - Get behavioral profile
    - [ ] `GET /recommendations/{user_id}` - Get recommendations
    - [ ] `POST /feedback` - Submit feedback
  - [ ] **Operator:**
    - [ ] `GET /operator/review` - Approval queue
    - [ ] `POST /operator/approve/{recommendation_id}` - Approve
    - [ ] `POST /operator/override/{recommendation_id}` - Override
    - [ ] `POST /operator/bulk_approve` - Bulk approve
    - [ ] `GET /operator/analytics` - System metrics
    - [ ] `GET /operator/feedback` - Aggregated feedback
  - [ ] **Evaluation:**
    - [ ] `GET /eval/metrics` - Retrieve metrics
    - [ ] `POST /eval/run` - Trigger evaluation
    - [ ] `GET /eval/fairness` - Fairness report
- [ ] Ensure local-only deployment (no cloud dependencies)
- [ ] Create single-command setup and startup:
  - [ ] `python run.py --setup` (install dependencies, init DB)
  - [ ] `python run.py --start` (start backend + frontend)
- [ ] Write comprehensive README with:
  - [ ] Setup instructions
  - [ ] Usage examples
  - [ ] API documentation
  - [ ] Architecture overview
  - [ ] Troubleshooting guide

## Phase 9: Testing & Documentation
- [ ] Write unit tests (15 minimum):
  - [ ] Subscription detection with jitter
  - [ ] Recurring merchant identification
  - [ ] Savings growth rate calculation
  - [ ] Credit utilization formula
  - [ ] Emergency fund coverage
  - [ ] Payroll detection accuracy
  - [ ] Income variability computation
  - [ ] Persona criteria boundary testing (each persona)
  - [ ] Consent enforcement (block without consent)
  - [ ] Eligibility filter logic
  - [ ] Tone check (negative phrase detection)
  - [ ] Rationale generation format
  - [ ] Window boundary date calculations
  - [ ] Partial window handling (<30 days)
  - [ ] Edge case: zero transactions in window
- [ ] Write integration tests (8 minimum):
  - [ ] End-to-end: ingest → signals → persona → recommendations
  - [ ] Multiple personas matching → prioritization
  - [ ] Consent revocation → recommendations disappear
  - [ ] User with multiple credit cards → aggregated signals
  - [ ] Feedback submission → storage → retrieval
  - [ ] Operator override flow
  - [ ] API authentication and authorization
  - [ ] Window rolling (data from day N vs N+1)
- [ ] Write edge case tests (5 minimum):
  - [ ] New user (<7 days data)
  - [ ] User with only pending transactions
  - [ ] Account with $0 balance entire period
  - [ ] User with negative savings growth
  - [ ] Simultaneous persona criteria changes
- [ ] Write performance tests (2 minimum):
  - [ ] Generate recommendations for 100 users <5 seconds each
  - [ ] Operator dashboard loads all signals <3 seconds
- [ ] **Total: ≥30 tests passing**
- [ ] Document schemas in `/docs/schema.md` with examples
- [ ] Write decision log in `/docs/decision_log.md`:
  - [ ] Why rolling windows vs fixed calendar periods
  - [ ] Persona prioritization rationale
  - [ ] Signal strength tie-breaker formula
  - [ ] Graceful degradation strategy for new users
  - [ ] Consent model choice (all-or-nothing)
  - [ ] Fairness approach (behavior-based, no demographics)
  - [ ] LLM integration strategy (optional with fallback)
  - [ ] Caching strategy and TTL reasoning
- [ ] Document all AI prompts in `/docs/ai_prompts.md` (if LLM used)
- [ ] Record evaluation results in `/docs/evaluation_results.md`
- [ ] Add "not financial advice" disclaimers throughout
- [ ] Verify all documentation is complete and clear

## Phase 10: A/B Testing (Optional Enhancement)
- [ ] Design A/B testing framework:
  - [ ] Infrastructure for variant assignment (50/50 split)
  - [ ] Track which users see which variant
  - [ ] Store variant-specific metrics
- [ ] Test rationale phrasings:
  - [ ] Variant A: Technical language
  - [ ] Variant B: Conversational language
  - [ ] Measure engagement rate difference
- [ ] Test education content effectiveness:
  - [ ] Different article titles/descriptions
  - [ ] Measure "This helped me" rate
- [ ] Test offer presentation:
  - [ ] Different CTA buttons
  - [ ] Measure click-through rate
- [ ] Implement statistical significance testing:
  - [ ] Chi-square test for categorical outcomes
  - [ ] Minimum sample size calculation
  - [ ] Confidence intervals
- [ ] Generate A/B test reports:
  - [ ] Winner declaration
  - [ ] Effect size
  - [ ] Recommendations for rollout
- [ ] Document A/B testing methodology and results

---

## Completion Checklist

### Code Quality
- [ ] All modules follow clear structure (`ingest/`, `features/`, `personas/`, etc.)
- [ ] One-command setup: `python run.py --setup`
- [ ] One-command start: `python run.py --start`
- [ ] ≥30 unit/integration tests passing
- [ ] Deterministic behavior (seeds for randomness)
- [ ] Error handling throughout
- [ ] No external dependencies (local-only)

### Documentation
- [ ] README with setup and usage instructions
- [ ] `/docs/decision_log.md` complete
- [ ] `/docs/schema.md` with examples
- [ ] `/docs/persona_criteria.md` detailed
- [ ] `/docs/limitations.md` explicit
- [ ] `/docs/ai_prompts.md` (if LLM used)
- [ ] `/docs/evaluation_results.md` with metrics

### Success Criteria
- [ ] 100% coverage (users with persona + ≥3 behaviors)
- [ ] 100% explainability (recommendations with rationales)
- [ ] <5 seconds latency per user
- [ ] 100% auditability (decision traces)
- [ ] >70% helpfulness score (from user feedback)
- [ ] No systematic bias in fairness analysis

### Deliverables
- [ ] Code repository (GitHub)
- [ ] Technical writeup (1-2 pages)
- [ ] Demo video or live presentation
- [ ] Performance metrics and benchmarks
- [ ] Test cases and validation results
- [ ] Data model/schema documentation
- [ ] Evaluation report (JSON/CSV + summary)

---

## Notes
- Prioritize transparency and explainability over sophistication
- User control and consent are paramount
- Education over sales pitch
- Fairness built in from day one (behavior-based only)
- Graceful degradation for edge cases
- All recommendations require plain-language rationales
