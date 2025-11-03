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
- User-facing web dashboard

### Scope
- Local-only deployment
- Synthetic dataset (50-100 users)
- Modular, rules-based baseline; optional LLM enhancements
- REST API + web-based operator dashboard + user web dashboard

---

## Features

### 1. Data Layer
**Synthetic data generation:**
- 50-100 users, diverse income and account types
- Transactions, accounts, and liabilities
- Realistic payroll simulation: monthly, semi-monthly, biweekly

**Realistic variability:**
- Subscriptions: ±1-2 day jitter, annual cadences, 10% cancellation rate, 5% price changes
- Seasonal patterns: holiday spending (Dec +30%), tax refunds (Apr), back-to-school (Aug/Sep)
- Life events: job changes (5%), major purchases (3%), medical expenses (10%), rent increases (2%)
- Edge cases: overdrafts, refunds, chargebacks, pending transactions, ATM withdrawals

**Storage:**
- SQLite for relational data
- Parquet for analytics
- JSON for configs/logs

### 2. Behavioral Signal Detection
**Time windows:**
- **30-day window:** [today - 30 days, today - 1 day] (excludes today's pending)
- **180-day window:** [today - 180 days, today - 1 day]
- Windows recalculate daily at midnight UTC
- Only settled transactions counted
- Graceful degradation for new users:
  - <7 days: "Welcome" persona, basic education
  - 7-29 days: Preliminary insights with disclaimer
  - 30+ days: Full 30-day analysis
  - 180+ days: Long-term window analysis

**Signals:**
- **Subscriptions:** recurring spend, share of total spend, merchant identification
- **Savings:** net inflow, growth rate, emergency fund coverage
- **Credit:** utilization, overdue status, interest charges, minimum payment detection
- **Income Stability:** payroll detection, frequency variability, cash-flow buffer

### 3. Persona Assignment
**5 Personas with prioritization:**

**Priority 1 - High Utilization (Urgent)**
- Criteria: Any card utilization ≥50% OR interest charges > 0 OR minimum-payment-only OR is_overdue = true
- Focus: Reduce utilization and interest; payment planning and autopay education

**Priority 2 - Variable Income Budgeter (Stability)**
- Criteria: Median pay gap > 45 days AND cash-flow buffer < 1 month
- Focus: Percent-based budgets, emergency fund basics, smoothing strategies

**Priority 3 - Credit Invisible / Builder (Foundation)**
- Criteria: No credit card accounts OR all cards $0 balance for 180+ days, AND has checking/savings accounts
- Focus: Credit basics education, secured cards, credit-building strategies, misconception correction

**Priority 4 - Subscription-Heavy (Optimization)**
- Criteria: Recurring merchants ≥3 AND (monthly recurring spend ≥$50 in 30d OR subscription spend share ≥10%)
- Focus: Subscription audit, cancellation/negotiation tips, bill alerts

**Priority 5 - Savings Builder (Growth)**
- Criteria: Savings growth rate ≥2% over window OR net savings inflow ≥$200/month, AND all card utilizations < 30%
- Focus: Goal setting, automation, APY optimization (HYSA/CD basics)

**Prioritization logic:**
1. Apply priority order above (Priority 1 = highest urgency)
2. If multiple personas at same priority level, select based on signal strength (strongest behavioral indicators)
3. If still tied, use defined order: High Utilization → Variable Income → Credit Builder → Subscription-Heavy → Savings Builder
4. Assign single primary persona per user
5. Log all matching personas and selection rationale in decision trace

### 4. Recommendations
**Education content catalog (3-5 items per user):**

**High Utilization:**
- "Avalanche vs Snowball: Debt Paydown Strategies"
- "How Credit Utilization Affects Your Score"
- "Setting Up Autopay to Avoid Late Fees"
- "Balance Transfer Cards: Pros and Cons"
- "Creating a Debt Payoff Timeline"

**Variable Income Budgeter:**
- "Percent-Based Budgeting for Irregular Income"
- "Building a 3-Month Emergency Fund"
- "Smoothing Income with Savings Buffers"
- "Essential vs Discretionary: Priority Spending"
- "Cash Flow Forecasting Basics"

**Credit Invisible / Builder:**
- "Credit 101: How Credit Works"
- "Secured Credit Cards Explained"
- "Building Credit Without Going Into Debt"
- "Credit Myths Debunked"
- "When to Use Credit vs Debit"

**Subscription-Heavy:**
- "The $200 Subscription Audit Checklist"
- "Negotiating Lower Bills: Scripts That Work"
- "Setting Up Subscription Alerts"
- "Free Alternatives to Paid Services"
- "Annual vs Monthly: The True Cost"

**Savings Builder:**
- "SMART Goal Setting for Savings"
- "Automating Savings: Set It and Forget It"
- "High-Yield Savings Accounts Explained"
- "CD Laddering for Better Returns"
- "Emergency Fund vs Investment: What Goes Where"

**Partner offers (1-3 per user with eligibility):**
- Balance transfer credit cards (if utilization ≥30%, credit score proxy ≥650)
- High-yield savings accounts (if building emergency fund, no existing HYSA)
- Budgeting apps (if variable income, no existing linked app)
- Subscription management tools (if ≥5 subscriptions)
- Secured credit cards (if credit invisible, checking account balance ≥$500)

**Rationale format:**
Every recommendation includes plain-language "because" statement citing specific data:
- "We noticed your Visa ending in 4523 is at 68% utilization ($3,400 of $5,000 limit). Bringing this below 30% could improve your credit score and reduce interest charges of $87/month."
- "You have 7 active subscriptions totaling $143/month. An audit could help identify services you no longer use."

**Optional LLM integration:**
- Dynamic content generation for variety
- Personalized rationale phrasing
- Fallback to static catalog if LLM unavailable

### 5. Guardrails
**Consent:**
- All-or-nothing explicit opt-in required before processing
- Users can revoke consent anytime (immediate effect)
- Track consent status per user in database
- No recommendations generated without active consent

**Eligibility:**
- Don't recommend products user isn't eligible for
- Check minimum income/credit requirements
- Filter based on existing accounts (no HYSA offer if they have one)
- Avoid harmful products (no payday loans, predatory lenders)

**Tone:**
- No shaming language ("you're overspending", "bad choices")
- Empowering, educational tone
- Neutral, supportive phrasing
- Automated tone checks with blocklist of negative phrases

**Disclosure:**
Every recommendation includes: "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."

### 6. User Experience
**Web Dashboard (User-Facing):**
- **Header:** Welcome message with user's primary persona
- **Insights Card:** Top 3 behavioral signals with plain-language explanations
- **Your Plan:** 3-5 education items with rationale, priority ordering
- **Offers:** 1-3 partner offers with eligibility badges and disclaimers
- **Feedback:** Thumbs up/down on each recommendation, "This helped me" / "Not relevant" buttons
- **Action Tracking:** "I applied this" / "Already doing this" options
- **Progress View:** (if applicable) Changes in signals over time, persona transitions

**Feedback system:**
- Thumbs up/down on each recommendation
- "This helped me" / "Not relevant" / "I applied this" / "Already doing this"
- Optional free-text feedback (<200 chars)
- Feedback stored per recommendation per user

**Data requirements:**
- Display disclaimers prominently
- Show data freshness (last updated timestamp)
- Link to consent management
- Explanation of how insights are generated

### 7. Operator View
**Web-based dashboard features:**

**User Review:**
- Search by user ID
- Filter by persona
- View detected signals (30d and 180d windows)
- See primary persona + all matching personas
- Review generated recommendations with rationales
- Decision trace visibility (why this persona, why these recommendations)

**Approval Queue:**
- List of pending recommendations requiring review
- Approve or override functionality
- Bulk actions: approve all for a persona, approve selected
- Flag recommendations for manual review
- Add operator notes

**Analytics View:**
- Persona distribution chart
- Signal detection rates
- Recommendation generation metrics
- User engagement rates (feedback aggregated)
- Coverage and explainability dashboards

**Feedback Review:**
- Aggregate thumbs up/down by recommendation type
- Filter by persona or content category
- Identify low-performing content
- Track "I applied this" action rates

**System Health:**
- Latency monitoring (recommendation generation time)
- Error logs and data quality alerts
- Consent status overview

### 8. Evaluation & Metrics
**Automatic scoring:**
- **Coverage:** % of users with assigned persona + ≥3 detected behaviors (target: 100%)
- **Explainability:** % of recommendations with plain-language rationales (target: 100%)
- **Relevance:** Rules-based scoring of education-persona fit
- **Latency:** Time to generate recommendations per user (target: <5 seconds)
- **Auditability:** % of recommendations with decision traces (target: 100%)

**User satisfaction (from feedback):**
- **Engagement Rate:** % of recommendations interacted with
- **Helpfulness Score:** thumbs up / (thumbs up + thumbs down)
- **Action Rate:** % marked "I applied this"

**Fairness (behavior-based, no demographics):**
- Persona distribution across income quartiles (detected from payroll)
- Average recommendation count by income level
- Offer eligibility rates by account complexity (basic vs full suite)
- Tone sentiment analysis across all personas
- Ensure low-income users not systematically excluded

**Output:**
- JSON/CSV metrics files
- Charts and graphs (persona distribution, engagement trends)
- Brief summary report (1-2 pages)
- Per-user decision traces
- Fairness analysis report

### 9. API Endpoints
**User Management:**
- `POST /users` - Create user with synthetic data
- `POST /consent` - Record consent (opt-in)
- `DELETE /consent/{user_id}` - Revoke consent
- `GET /consent/{user_id}` - Check consent status

**Data & Analysis:**
- `GET /profile/{user_id}` - Get behavioral profile (signals, persona)
- `GET /recommendations/{user_id}` - Get recommendations with rationales
- `POST /feedback` - Record user feedback (thumbs up/down, action taken)

**Operator:**
- `GET /operator/review` - Operator approval queue
- `POST /operator/approve/{recommendation_id}` - Approve recommendation
- `POST /operator/override/{recommendation_id}` - Override with custom content
- `GET /operator/analytics` - System analytics and metrics
- `GET /operator/feedback` - Aggregated user feedback

**Evaluation:**
- `GET /eval/metrics` - Retrieve evaluation metrics
- `POST /eval/run` - Trigger evaluation run

---

## Technology Stack
- **Backend:** Python (Flask/FastAPI)
- **Database:** SQLite (relational), Parquet (analytics)
- **Frontend:** Web-based dashboard (React/Vue or static HTML+JS)
- **API:** REST
- **Storage:** Local only, no cloud dependencies
- **Optional:** LLM integration for dynamic content (OpenAI API, Anthropic Claude, or local model)

---

## Phased Build Strategy

### Phase 1: Data Foundation
- Generate synthetic dataset with realistic variability
- Validate schemas
- Implement CSV/JSON ingestion

### Phase 2: Feature Engineering
- Partition transactions into 30d and 180d windows
- Compute behavioral signals
- Handle edge cases (new users, partial windows)

### Phase 3: Persona System
- Implement 5 personas with criteria
- Build prioritization and tie-breaking logic
- Document decision traces

### Phase 4: Recommendation Engine
- Build education content catalog
- Implement dynamic partner offers with eligibility
- Generate plain-language rationales
- Optional LLM integration

### Phase 5: Guardrails & UX
- Implement consent tracking and enforcement
- Build eligibility and tone checks
- Create user-facing web dashboard
- Implement feedback system

### Phase 6: Operator Dashboard
- Build operator view with review functionality
- Implement approval queue and bulk actions
- Create analytics view
- Add feedback review interface

### Phase 7: Evaluation & Metrics
- Build automatic scoring system
- Generate fairness analysis
- Create charts and reports
- Document limitations

### Phase 8: API & Deployment
- Implement all REST endpoints
- Ensure local-only deployment
- Single-command setup
- Write comprehensive README

### Phase 9: Testing & Documentation
- Unit and integration tests (≥30 total)
- Document schemas, decision log, AI prompts
- Include disclaimers
- Record evaluation results

### Phase 10: A/B Testing (Optional Enhancement)
- Framework for testing rationale phrasings
- Compare education content effectiveness
- Measure engagement with offer types
- Statistical significance testing

---

## Success Criteria

| Category | Metric | Target |
|----------|--------|--------|
| Coverage | Users with persona + ≥3 behaviors | 100% |
| Explainability | Recommendations with rationales | 100% |
| Latency | Time per user recommendation | <5 seconds |
| Auditability | Recommendations with decision traces | 100% |
| Code Quality | Passing unit/integration tests | ≥30 tests |
| Documentation | Schema and decision log clarity | Complete |
| User Satisfaction | Helpfulness score | >70% |
| Fairness | Equitable access across income levels | No systematic bias |

---

## Key Design Principles
- **Transparency over sophistication:** Every decision must be explainable
- **User control over automation:** Consent is paramount
- **Education over sales:** Help users learn, don't just push products
- **Fairness built in from day one:** Behavior-based only, no demographic discrimination
- **Graceful degradation:** System works even with limited data

---

## Documentation Structure
```
/docs
  ├── decision_log.md          # Key architectural choices and rationale
  ├── schema.md                # Database schemas with examples
  ├── persona_criteria.md      # Detailed persona rules and edge cases
  ├── limitations.md           # Known limitations and assumptions
  ├── ai_prompts.md            # LLM prompts if used
  ├── evaluation_results.md    # Final metrics and fairness analysis
  └── testing_strategy.md      # Test cases and coverage report
```

---

## Explicit Limitations
- No real-time Plaid integration (synthetic data only)
- Rules-based baseline (LLM optional, not required)
- Local deployment only (not production-ready)
- Simplified eligibility logic (no real credit checks)
- Educational content, not regulated financial advice
- No guarantee of recommendation quality for real users
