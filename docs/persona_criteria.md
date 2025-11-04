# Persona Criteria Documentation

This document details the criteria, logic, and edge cases for persona assignment in SpendSense.

## Persona Overview

SpendSense assigns users to one of five personas based on their financial behavior. Personas are prioritized by urgency, with higher-priority personas addressing more urgent financial needs.

## Persona Definitions

### Priority 1: High Utilization (Urgent)

**Focus:** Debt reduction and credit management

**Criteria:**
- Any credit card utilization ≥50% OR
- Interest charges > $0 OR
- Minimum-payment-only pattern detected OR
- Account is overdue

**Rationale:** High credit utilization and interest charges indicate urgent financial stress. This persona takes highest priority to address immediate debt concerns.

**Edge Cases:**
- Multiple credit cards: Uses highest utilization across all cards
- Zero utilization with interest: Matches if interest charges exist (balance transfer fees, etc.)
- Pending payments: Overdue status checked from liabilities table

### Priority 2: Variable Income Budgeter (Stability)

**Focus:** Income smoothing and cash flow management

**Criteria:**
- Median pay gap > 45 days AND
- Cash-flow buffer < 1 month

**Rationale:** Irregular income with insufficient buffer creates financial instability. Users need help with budgeting for variable income.

**Edge Cases:**
- No payroll detected: If no payroll deposits found, median_gap = 0, doesn't match
- Single paycheck: Needs at least 2 paychecks to calculate gap
- High income, low buffer: Still matches if gap > 45 days and buffer < 1 month

### Priority 3: Credit Builder (Foundation)

**Focus:** Building credit history and understanding credit basics

**Criteria:**
- No credit card accounts OR
- All credit cards have $0 balance for 180+ days AND
- Has checking/savings accounts (implicitly required)

**Rationale:** Users without active credit usage need foundational credit education. This is a foundational need but less urgent than debt issues.

**Edge Cases:**
- No accounts: Credit builder requires checking/savings accounts
- Zero balance cards: Matches if utilization is 0% and no credit activity
- Recent credit cards: If cards exist but unused, still matches

### Priority 4: Subscription-Heavy (Optimization)

**Focus:** Subscription management and optimization

**Criteria:**
- Recurring merchants ≥3 AND
- (Monthly recurring spend ≥$50 OR subscription spend share ≥10%)

**Rationale:** Multiple subscriptions with significant spend indicate optimization opportunity. Lower priority as it's about optimization, not urgent need.

**Edge Cases:**
- Annual subscriptions: Counted in recurring merchants if detected
- Canceled subscriptions: Only active subscriptions counted
- High spend, low count: Needs both ≥3 merchants AND ≥$50/month or ≥10% share

### Priority 5: Savings Builder (Growth)

**Focus:** Savings growth and investment strategies

**Criteria:**
- (Savings growth rate ≥2% OR net savings inflow ≥$200/month) AND
- All credit card utilizations < 30%

**Rationale:** Users building savings while maintaining healthy credit deserve growth-focused guidance. Lowest priority as it's about growth, not urgent need.

**Edge Cases:**
- Negative growth: Growth rate must be ≥2% (positive growth)
- High utilization: Doesn't match if any card ≥30% utilization
- Multiple savings accounts: Aggregates across all savings accounts

## Prioritization Logic

### Step 1: Priority Order
Personas are first filtered by priority level (1 = highest urgency). If multiple personas match, select from the highest priority group.

### Step 2: Signal Strength Tie-Breaker
If multiple personas match at the same priority level, calculate signal strength for each:

**Signal Strength Formula:**
- Sum of normalized signal values (0-1 scale)
- Each signal type normalized based on relevant ranges:
  - Utilization: 0-100% → 0-1
  - Interest charges: 0-500 → 0-1
  - Subscription count: 0-10 → 0-1
  - Savings growth: -10% to 20% → 0-1
  - Income gap: 0-90 days → 0-1

### Step 3: Defined Order Tie-Breaker
If signal strengths are equal, use defined order:
1. High Utilization
2. Variable Income Budgeter
3. Credit Builder
4. Subscription-Heavy
5. Savings Builder

## Assignment Workflow

1. **Signal Computation:** Compute all behavioral signals for user
2. **Persona Matching:** Match user to all applicable personas
3. **Priority Selection:** Select highest priority group
4. **Tie-Breaking:** Use signal strength, then defined order
5. **Assignment:** Assign single primary persona
6. **Logging:** Store decision trace with rationale

## Decision Trace Format

Each persona assignment includes a decision trace (JSON) with:
- `reason`: Why this persona was selected
- `matched_personas`: All personas that matched
- `highest_priority`: Priority level of selected persona
- `signal_strengths`: Strength values for each candidate
- `selected_persona`: Final selection
- `data_availability`: User's data availability classification

## Graceful Degradation

### New Users (<7 days)
- Assigned "Welcome" persona (special priority 0)
- No persona matching performed
- Basic financial education only

### Limited Data (7-29 days)
- Persona matching performed with limited data
- Disclaimer displayed about preliminary insights

### Full Data (30+ days)
- Full persona matching with 30-day window
- Standard assignment logic applied

### Extended Data (180+ days)
- Full persona matching with both 30d and 180d windows
- Uses 180d window for persona assignment (more stable)

## Testing Considerations

### Test Cases
1. **High Utilization:** User with 60% utilization, $100/month interest
2. **Variable Income:** User with 60-day pay gaps, 0.5 month buffer
3. **Credit Builder:** User with no credit cards, has checking/savings
4. **Subscription-Heavy:** User with 5 subscriptions, $75/month
5. **Savings Builder:** User with 5% growth, 15% utilization

### Edge Cases
- No matches: Defaults to Credit Builder (should be rare)
- Multiple high-priority matches: Uses signal strength
- Tied signal strengths: Uses defined order
- New users: Welcome persona (no matching)

## Known Limitations

1. **Credit Builder Detection:** Currently relies on utilization = 0. Full implementation should check account existence in database.
2. **Minimum Payment Detection:** Simplified logic; full implementation would analyze payment history patterns.
3. **Income Detection:** May miss payroll if merchant names don't match patterns.
4. **Subscription Detection:** Requires 3+ transactions in 90 days; may miss annual subscriptions.

## Future Improvements

1. Machine learning-based persona assignment (optional enhancement)
2. Multi-persona recommendations (show all applicable personas)
3. Persona transition tracking (how users move between personas over time)
4. Confidence scoring for persona assignments

