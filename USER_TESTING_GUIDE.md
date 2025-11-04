# SpendSense User Testing Guide

This guide provides scenarios and tools for testing SpendSense from a user perspective.

## Quick Start

### Interactive Tools

1. **User Dashboard View** - Simulate viewing recommendations as a user
   ```bash
   python3 user_view.py <user_id>
   # Example: python3 user_view.py user_001
   ```

2. **Interactive Testing Menu** - Menu-driven interface
   ```bash
   python3 interactive_test.py
   ```

3. **User Testing Scenarios** - Structured test scenarios
   ```bash
   python3 user_testing_scenarios.py
   # Or run specific scenario:
   python3 user_testing_scenarios.py 1  # New User Journey
   python3 user_testing_scenarios.py 2  # Feedback Collection
   python3 user_testing_scenarios.py 3  # Consent Revocation
   python3 user_testing_scenarios.py 4  # Different Personas
   python3 user_testing_scenarios.py 5  # System Health
   ```

## Available Test Scenarios

### Scenario 1: New User Journey

**Purpose:** Test the complete onboarding flow for a new user

**Steps:**
1. User views dashboard without consent
2. User provides consent
3. System assigns persona
4. System generates recommendations
5. User views recommendations

**Expected Behavior:**
- Consent required message shown initially
- After consent, persona assigned automatically
- Recommendations generated based on persona
- All recommendations have rationales

**Run:**
```bash
python3 user_testing_scenarios.py 1
```

### Scenario 2: Feedback Collection

**Purpose:** Test user feedback functionality

**Steps:**
1. User views recommendations
2. User provides feedback (thumbs up/down, helpful, applied)
3. System stores feedback
4. Review feedback summary

**Expected Behavior:**
- Feedback can be submitted for any recommendation
- Multiple feedback types supported (thumbs, helpful, applied)
- Feedback stored and retrievable
- Statistics aggregated correctly

**Run:**
```bash
python3 user_testing_scenarios.py 2
```

### Scenario 3: Consent Revocation

**Purpose:** Test consent revocation and data deletion

**Steps:**
1. Check user has consent and recommendations
2. User revokes consent
3. Verify recommendations are deleted
4. Verify user cannot access recommendations

**Expected Behavior:**
- Consent revocation works
- All recommendations deleted immediately
- User cannot access recommendations without consent

**Run:**
```bash
python3 user_testing_scenarios.py 3
```

### Scenario 4: Different Personas

**Purpose:** Explore different persona assignments and recommendations

**Steps:**
1. View persona distribution
2. Examine users for each persona
3. Review recommendations for different personas

**Expected Behavior:**
- Different personas show different recommendations
- Recommendations match persona criteria
- Persona distribution reflects user behavior

**Run:**
```bash
python3 user_testing_scenarios.py 4
```

### Scenario 5: System Health

**Purpose:** Check system metrics and health

**Steps:**
1. View coverage metrics
2. View engagement metrics
3. View system health status

**Expected Behavior:**
- Metrics calculated correctly
- Health status accurate
- Performance within targets

**Run:**
```bash
python3 user_testing_scenarios.py 5
```

## User Dashboard Testing

### View User Dashboard

```bash
python3 user_view.py user_001
```

**What to Test:**
- ✅ Consent check (shows message if no consent)
- ✅ Persona display
- ✅ Behavioral signals display
- ✅ Recommendations list (education + offers)
- ✅ Rationales present
- ✅ Data freshness information
- ✅ Disclaimers present

### List Available Users

```bash
python3 user_view.py
```

Shows list of available users for testing.

## Interactive Testing

### Menu-Driven Interface

```bash
python3 interactive_test.py
```

**Features:**
1. View User Dashboard
2. Test Consent Flow
3. View Persona Assignment
4. Generate Recommendations
5. Submit Feedback
6. View Operator Analytics
7. View User Profile (Operator View)
8. Run End-to-End Test
9. Exit

## Testing Checklist

### Consent Flow
- [ ] User cannot view recommendations without consent
- [ ] Consent opt-in works
- [ ] Consent opt-out works
- [ ] Recommendations deleted on opt-out
- [ ] Consent status persists

### Recommendations
- [ ] Recommendations generated based on persona
- [ ] All recommendations have rationales
- [ ] Education content matches persona
- [ ] Partner offers have eligibility checks
- [ ] Recommendations pass guardrails (tone, eligibility, disclosure)

### Feedback
- [ ] Can submit thumbs up/down
- [ ] Can mark "helped me"
- [ ] Can mark "applied this"
- [ ] Free text feedback works
- [ ] Feedback stored correctly
- [ ] Feedback retrievable

### Personas
- [ ] All 5 personas can be assigned
- [ ] Persona prioritization works
- [ ] Signal strength tie-breaking works
- [ ] Decision traces logged
- [ ] Recommendations match persona

### Edge Cases
- [ ] New user (<7 days data) handled gracefully
- [ ] User with only pending transactions
- [ ] User with zero balance
- [ ] User with negative savings
- [ ] User with no transactions

## Current System State

Based on latest test run:

- **Total Users:** 100
- **Users with Consent:** 10
- **Users with Personas:** 45
- **Total Recommendations:** 394

## Sample User IDs

- `user_001` - Credit Builder persona
- `user_002` - Credit Builder persona
- `user_008` - Savings Builder persona
- `user_010` - Subscription-Heavy persona
- `user_011` - Credit Builder persona (newly tested)

## Testing Tips

1. **Start with Scenario 1** - Ensures user has consent and recommendations
2. **Use different users** - Test different personas and behaviors
3. **Check feedback** - Verify feedback is stored and aggregated
4. **Test edge cases** - Try users with minimal data
5. **Review metrics** - Check system health and coverage

## Troubleshooting

### "No users found"
- Run `python3 run.py --setup` to generate data

### "No recommendations"
- Ensure user has consent: `python3 interactive_test.py` → Option 2
- Generate recommendations: `python3 interactive_test.py` → Option 4

### "User not found"
- Check available users: `python3 user_view.py`
- Use existing user IDs from the list

## Next Steps

After user testing:

1. Review feedback metrics
2. Check system health
3. Test edge cases
4. Verify all personas work
5. Validate guardrails
6. Review performance metrics

---

**Happy Testing!** 🚀

