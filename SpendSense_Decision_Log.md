# SpendSense Decision Log

This document records key architectural and design decisions made during the development of SpendSense, along with the rationale behind each choice.

---

## 1. Time Window Strategy

**Decision:** Rolling daily windows with fixed lookback periods (30 days and 180 days)

**Rationale:**
- **Rolling vs Fixed Calendar:** Rolling windows provide more consistent and fair comparisons across users who start at different times. Fixed calendar windows (e.g., "this month") would create artificial discontinuities at month boundaries and disadvantage users who sign up mid-month.
- **Daily Recalculation:** Windows update daily at midnight UTC to ensure fresh insights while maintaining computational efficiency. Real-time updates would be computationally expensive and provide marginal value.
- **Lookback Exclusion:** We exclude "today" (today-1 as the end date) to avoid inconsistencies from pending transactions and intraday volatility.
- **Dual Windows:** 30-day captures recent behavior changes; 180-day provides long-term pattern stability. This allows detection of both emerging issues and sustained positive behaviors.

**Alternatives Considered:**
- Fixed calendar months: Rejected due to unfairness to mid-month signups
- Real-time continuous windows: Rejected due to computational cost without meaningful benefit
- Single window (90 days): Rejected because it misses both short-term urgency and long-term trends

**Edge Cases Handled:**
- Pending transactions excluded to avoid double-counting when they settle
- Transactions on exact boundary dates follow clear rules (inclusive start, exclusive end)

---

## 2. Persona Prioritization Hierarchy

**Decision:** Five-level priority system with signal-strength tie-breaking

**Priority Order:**
1. High Utilization (urgent debt/credit issues)
2. Variable Income Budgeter (stability risk)
3. Credit Invisible/Builder (foundational need)
4. Subscription-Heavy (optimization opportunity)
5. Savings Builder (growth phase)

**Rationale:**
- **Safety First:** Financial risk and debt issues take precedence over optimization
- **Maslow-Style Hierarchy:** Address stability before growth
- **Actionability:** Higher priorities correspond to more urgent, impactful interventions
- **Signal Strength Tie-Breaker:** If multiple personas at same priority, select the one with strongest behavioral signals (sum of normalized signal values)
- **Final Tie-Breaker:** If signal strength equal, use defined order for deterministic behavior

**Alternatives Considered:**
- No prioritization (show all matching): Rejected due to user overwhelm
- User-selected priority: Rejected because users may not recognize urgency
- Machine learning ranking: Rejected to maintain explainability in baseline

**Example:**
- User matches both Variable Income (Priority 2) and Subscription-Heavy (Priority 4)
- Select Variable Income because Priority 2 > Priority 4
- If user matched Variable Income and Credit Builder (both different priorities), pick Variable Income
- If user matched two Priority 4 personas, calculate signal strength and pick stronger

---

## 3. Graceful Degradation for New Users

**Decision:** Tiered experience based on data availability

**Tiers:**
- **<7 days:** "Welcome" persona with universal financial literacy content
- **7-29 days:** Preliminary insights with clear disclaimer ("We'll have better insights after 30 days")
- **30+ days:** Full 30-day window analysis
- **180+ days:** Add long-term trend analysis

**Rationale:**
- **No User Left Behind:** Even brand-new users get value (basic education)
- **Transparency:** Clear communication about confidence level
- **Avoid False Signals:** Short-term data can be misleading (e.g., one paycheck looks like "variable income")
- **Progressive Enhancement:** As more data arrives, insights improve naturally

**Alternatives Considered:**
- Block all insights until 30 days: Rejected due to poor new user experience
- Treat all users equally: Rejected due to risk of false positives with insufficient data
- Require manual review for <30 days: Rejected due to scalability issues

---

## 4. Consent Model Choice

**Decision:** All-or-nothing consent for data processing and recommendations

**Rationale:**
- **Simplicity:** Easier for users to understand—one clear choice
- **Legal Safety:** Reduces risk of partial consent being insufficient for certain processing
- **Implementation Efficiency:** Single boolean flag vs complex granular permissions
- **Clear User Control:** Users know exactly what they're agreeing to

**Alternatives Considered:**
- Granular consent (analysis vs partner offers): Rejected due to complexity and potential user confusion
- Opt-out (process by default): Rejected due to privacy concerns
- Progressive consent (ask per feature): Rejected due to user fatigue

**Consent Requirements:**
- Explicit opt-in required before any processing
- Revocation takes immediate effect (recommendations disappear)
- Tracked per user with timestamp
- Displayed prominently in UI

---

## 5. Persona 5 Selection: Credit Invisible/Builder

**Decision:** Choose "Credit Invisible/Builder" over alternatives like "Frugal Planner"

**Rationale:**
- **Distinct from Savings Builder:** Avoids overlap with existing persona
- **Underserved Population:** Many people avoid credit entirely, limiting financial options
- **Clear Educational Gap:** Credit misconceptions are common and addressable
- **Real-World Impact:** Credit history affects housing, employment, insurance rates
- **Actionable Interventions:** Secured cards, credit-building strategies have proven efficacy

**Criteria:**
- No credit card accounts OR all cards at $0 balance for 180+ days
- AND has checking/savings accounts (actively banking)
- AND no credit utilization flags

**Alternatives Considered:**
- Frugal Planner: Rejected due to overlap with Savings Builder
- Irregular Income Saver: Rejected due to overlap with Variable Income Budgeter
- Financial Newcomer: Rejected as too vague and hard to operationalize

---

## 6. Fairness Approach: Behavior-Based, No Demographics

**Decision:** Measure fairness based on detected income levels and account complexity, not demographic attributes

**Rationale:**
- **Anti-Discrimination:** Avoids protected class issues entirely
- **Behavioral Focus:** Aligns with core mission of pattern detection
- **Legally Defensible:** No collection or use of sensitive attributes
- **Practical Proxy:** Income quartiles (from payroll) capture financial capacity without demographic inference
- **Auditable:** Can verify no systematic bias without demographic data

**Fairness Metrics:**
- Persona distribution across income quartiles
- Average recommendation count by income level
- Offer eligibility rates by account complexity (basic checking vs full suite)
- Tone sentiment analysis across all personas

**Alternatives Considered:**
- Demographic parity (race, gender, age): Rejected due to discrimination risk and data unavailability
- Ignore fairness: Rejected as irresponsible for financial AI
- Equal outcomes enforcement: Rejected as potentially discriminatory in reverse

**Red Flags:**
- Low-income users systematically excluded from beneficial offers
- Certain personas disproportionately assigned to lower-income users
- Negative tone more frequent for certain income levels

---

## 7. Signal Strength Tie-Breaker Formula

**Decision:** Sum of normalized signal values to quantify behavioral strength

**Formula:**
```python
signal_strength = (
    normalize(subscription_count, 0, 10) +
    normalize(credit_utilization, 0, 100) +
    normalize(savings_growth_rate, -10, 20) +
    normalize(income_variability, 0, 90) +
    normalize(emergency_fund_months, 0, 12)
)
```

**Rationale:**
- **Comparable Across Signals:** Normalization puts different scales on common ground
- **Additive Logic:** More signals = stronger match
- **Transparent:** Simple sum is explainable to operators
- **Deterministic:** No randomness, reproducible results

**Alternatives Considered:**
- Weighted sum: Rejected to avoid subjective weighting
- Machine learning ranking: Rejected to maintain explainability
- First-match wins: Rejected as arbitrary and potentially unfair

---

## 8. LLM Integration Strategy

**Decision:** Optional LLM enhancement with static catalog fallback

**Rationale:**
- **Baseline Independence:** System works without LLM (rules-based catalog)
- **Enhanced Variety:** LLM can generate fresh rationales and educational content
- **Cost Management:** LLM only used when available and within budget
- **Reliability:** Static fallback ensures uptime
- **Explainability Maintained:** LLM-generated content still follows rationale format

**LLM Use Cases:**
- Dynamic rationale phrasing (avoid repetition)
- Personalized content generation
- A/B testing different explanation styles

**Guardrails:**
- Output validation (tone check, length limit)
- Fallback to static catalog on error
- Log all prompts and responses for auditing

**Alternatives Considered:**
- LLM-required: Rejected due to dependency risk and cost
- No LLM at all: Rejected as missing enhancement opportunity
- LLM for signal detection: Rejected due to explainability concerns

---

## 9. Caching Strategy and TTL

**Decision:** Cache computed signals per user per window with 24-hour TTL

**Rationale:**
- **Performance:** Pre-computed signals meet <5 second latency target
- **Daily Window Updates:** Signals only change once per day (at midnight UTC)
- **Memory Efficiency:** Cache only current window signals, not historical
- **Invalidation Logic:** New transactions trigger cache refresh

**Cache Structure:**
```python
cache_key = f"signals:{user_id}:{window_type}"  # e.g., "signals:user123:30d"
ttl = 24 * 60 * 60  # 24 hours in seconds
```

**Alternatives Considered:**
- No caching (compute on demand): Rejected due to latency concerns
- Longer TTL (week): Rejected due to stale data risk
- Shorter TTL (hourly): Rejected as unnecessary given daily window updates
- Database-level caching: Rejected in favor of application-level control

---

## 10. Synthetic Data Realism Techniques

**Decision:** Multi-layered realism with subscriptions, seasonality, life events, and edge cases

**Techniques Applied:**

**Subscription Variability:**
- ±1-2 day jitter on payment dates (realistic billing cycles)
- 10% cancellation rate mid-period
- 5% price increase probability
- Annual subscriptions (365-day cadence)
- Free trial → paid conversions

**Seasonal Patterns:**
- December: +30% discretionary spending (holidays)
- January: +15% subscription cancellations (New Year's resolutions)
- April: Tax refund deposits (~40% of users)
- August/September: Back-to-school spending spikes

**Life Events:**
- Job changes (5%): Payroll amount change, 60-day gap
- Major purchases (3%): $2K+ one-time transactions
- Medical expenses (10%): Unexpected healthcare costs
- Rent/mortgage increases (2%): Annual lease renewals

**Edge Cases:**
- Overdraft fees (NSF charges)
- Refunds (negative amounts)
- Chargebacks and reversals
- Pending transactions that never settle
- ATM withdrawals (cash spend invisible to system)

**Rationale:**
- **Test Robustness:** Edge cases expose bugs early
- **Realistic Behavior:** Patterns match real-world banking data
- **Signal Validation:** Confirms algorithms handle noise and variability
- **Reproducibility:** All randomness seeded for deterministic generation

---

## 11. Testing Strategy: 30+ Tests Across 4 Categories

**Decision:** Comprehensive test suite covering unit, integration, edge cases, and performance

**Test Breakdown:**
- **Unit Tests (15):** Individual signal computations, persona criteria, guardrails
- **Integration Tests (8):** End-to-end flows, multi-module interactions, API workflows
- **Edge Case Tests (5):** New users, zero balances, negative growth, pending-only data
- **Performance Tests (2):** Latency targets, bulk operations

**Rationale:**
- **Confidence:** High coverage ensures reliability
- **Regression Prevention:** Automated tests catch breaking changes
- **Documentation:** Tests serve as usage examples
- **Performance Validation:** Explicit latency checks ensure <5 second target

**Alternatives Considered:**
- Minimum 10 tests: Rejected as insufficient for production-quality code
- Manual testing only: Rejected due to error-proneness and time cost
- Test-driven development: Considered ideal but not mandated due to time constraints

---

## 12. User Feedback System Design

**Decision:** Multi-level feedback with thumbs up/down + action tracking

**Feedback Levels:**
1. **Thumbs up/down:** Quick sentiment (like/dislike)
2. **Helpfulness tags:** "This helped me" / "Not relevant"
3. **Action tracking:** "I applied this" / "Already doing this"
4. **Free-text:** Optional <200 chars for details

**Rationale:**
- **Granularity:** Different levels serve different analysis needs
- **Low Friction:** Thumbs up/down requires minimal effort
- **Actionable Insights:** "I applied this" tracks real-world impact
- **Continuous Improvement:** Feedback feeds evaluation and A/B testing

**Use Cases:**
- Identify low-performing content (high thumbs down)
- Track engagement rate (% interacting)
- Measure action rate (% applying advice)
- Discover content gaps (high "not relevant")

**Alternatives Considered:**
- No feedback: Rejected as missed learning opportunity
- Star ratings (1-5): Rejected due to complexity and interpretation ambiguity
- Required feedback: Rejected due to user friction

---

## 13. Operator Dashboard Scope

**Decision:** Four core views (User Review, Approval Queue, Analytics, Feedback) with bulk actions

**Views:**
1. **User Review:** Deep-dive into individual user signals, persona, recommendations
2. **Approval Queue:** Pending recommendations requiring human oversight
3. **Analytics:** System-wide metrics, persona distribution, engagement trends
4. **Feedback Review:** Aggregated user feedback for content optimization

**Rationale:**
- **Human Oversight:** Critical for financial recommendations (not fully automated)
- **Efficiency:** Bulk actions prevent bottlenecks
- **Data-Driven:** Analytics inform content and algorithm improvements
- **Trust Building:** Operator review catches edge cases and ensures quality

**Alternatives Considered:**
- Fully automated (no operator): Rejected due to risk in financial domain
- Minimal operator view: Rejected as insufficient oversight
- Separate tools per view: Rejected due to UX fragmentation

---

## 14. REST API Design Philosophy

**Decision:** RESTful endpoints with clear resource separation (users, consent, recommendations, operator, evaluation)

**Principles:**
- **Resource-Oriented:** Endpoints map to logical entities
- **Stateless:** No server-side session management
- **Standard HTTP Methods:** GET (retrieve), POST (create), DELETE (remove)
- **Versioning Ready:** API design allows future v2 without breaking v1

**Example Pattern:**
```
GET /recommendations/{user_id}  # Retrieve
POST /feedback                  # Create
DELETE /consent/{user_id}       # Remove
```

**Rationale:**
- **Familiarity:** REST is industry standard, easy to learn
- **Scalability:** Stateless design supports horizontal scaling
- **Tooling:** Standard HTTP clients work out-of-box
- **Documentation:** Clear resource structure self-documents

**Alternatives Considered:**
- GraphQL: Rejected due to complexity for simple use case
- gRPC: Rejected due to local-only deployment
- Custom RPC: Rejected in favor of standards

---

## 15. Local-Only Deployment Constraint

**Decision:** No cloud dependencies, all data and processing local

**Rationale:**
- **Privacy:** Sensitive financial data never leaves local machine
- **Project Scope:** Simplifies deployment and removes infrastructure concerns
- **Reproducibility:** Anyone can run identical setup
- **Cost:** Zero ongoing costs

**Implications:**
- SQLite instead of PostgreSQL/MySQL
- Local file storage instead of S3
- Optional LLM must be API-based or local model
- No authentication beyond basic operator access

**Alternatives Considered:**
- Cloud deployment: Rejected as out of scope for this project
- Hybrid (local data, cloud compute): Rejected due to privacy concerns

---

## 16. Limitations and Assumptions

**Documented Limitations:**
1. **No Real Plaid Integration:** Synthetic data only, not production-ready
2. **Simplified Eligibility:** No real credit checks or income verification
3. **Rules-Based Baseline:** More sophisticated ML possible but not required
4. **Educational Content Only:** Not regulated financial advice
5. **Local Deployment:** Not scalable to production without re-architecture
6. **Limited User Authentication:** Basic operator access only
7. **No Real-Time Updates:** Daily window recalculation, not instant
8. **Synthetic Edge Cases:** May not cover all real-world scenarios

**Assumptions:**
1. Users have at least one checking account
2. Payroll deposits are identifiable via ACH metadata
3. Merchants are consistently named across transactions
4. Credit card data includes utilization metrics
5. Users understand "educational content, not advice" disclaimer

---

## Summary

These decisions prioritize:
- **Explainability** over black-box sophistication
- **User control** over automation
- **Privacy** over convenience
- **Fairness** over raw performance
- **Transparency** over complexity

Every choice aims to build a trustworthy, auditable financial insights system that respects user agency and avoids discrimination.
