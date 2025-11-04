# Subscription Count Discrepancy - Root Cause and Fix

## Issue Description
The subscription count displayed in the **Behavioral Insights section** was different from the count shown in the **Active Subscriptions section**.

## Root Cause Analysis

### Two Different Issues Found

#### Issue 1: Different Query Logic

1. **Behavioral Insights Section** (Signal-based count)
   - Uses `SubscriptionDetector` class via the `/data/profile/{user_id}` endpoint
   - Processes transactions from the past **30 days** (30d signal window)
   - Finds **ALL merchants** with ≥3 transactions where span ≤90 days
   - No filtering by merchant name or category
   - Shows: "You have X recurring subscriptions"

2. **Active Subscriptions Section** (Original implementation)
   - Uses `/data/subscriptions/{user_id}` endpoint
   - **Previously had problems:**
     1. ❌ Filtered by hardcoded list of subscription merchants (Netflix, Spotify, etc.)
     2. ❌ Required all 3+ transactions within 30 days only
     3. ❌ More restrictive than the signal computation

#### Issue 2: Caching Discrepancy

- **Behavioral Insights Section**: Used **cached signals** with 24-hour TTL
  - If signals were computed 12 hours ago, it showed old subscription counts
  - New transactions since then wouldn't be reflected
  
- **Active Subscriptions Section**: Always queried **fresh data** from database
  - Always showed current subscription counts
  
- **Result**: Counts could differ if new transactions occurred since last signal computation

#### Issue 3: Date Range and Pending Transaction Mismatch ⚠️ CRITICAL

- **Behavioral Insights Section** (via TimeWindowPartitioner):
  - Date range: `[today-30, today-1]` (EXCLUDES today)
  - Filters: `pending = 0` (EXCLUDES pending transactions)
  
- **Active Subscriptions Section** (Original API):
  - Date range: `[today-30, today]` (INCLUDED today)
  - Filters: None (INCLUDED pending transactions)
  
- **Result**: If a merchant had:
  - A transaction today, OR
  - A pending transaction
  
  It would appear in Active Subscriptions but NOT in Behavioral Insights

### Why the Counts Were Different

**Problem 1: Query Logic Mismatch**
- The API endpoint was using **more restrictive logic** than the `SubscriptionDetector`:
  - **Filtering by merchant names**: Only showed known subscription services
  - **Wrong time window logic**: Required all 3+ transactions within 30 days
  - This caused legitimate recurring merchants to be excluded from the Active Subscriptions view

**Problem 2: Timing/Caching Issue**
- Signals were cached for 24 hours, but subscriptions endpoint always queried fresh data
- If new transactions occurred, the cached signals would show old counts while subscriptions showed new counts

**Problem 3: Date Range and Filtering Mismatch** ⚠️ **CRITICAL**
- Behavioral Insights used `[today-30, today-1]` and excluded pending transactions
- Active Subscriptions used `[today-30, today]` and included pending transactions
- This 1-day difference and pending inclusion caused the counts to differ by 1 or more

## The Fixes

### Fix 1: Aligned Query Logic

Updated `/data/subscriptions/{user_id}` endpoint to **exactly match** `SubscriptionDetector` logic:

```sql
-- New logic (matches SubscriptionDetector):
SELECT 
    merchant_name,
    COUNT(*) as transaction_count,
    AVG(ABS(amount)) as avg_amount,
    MIN(date) as first_transaction,
    MAX(date) as last_transaction,
    JULIANDAY(MAX(date)) - JULIANDAY(MIN(date)) as day_span
FROM transactions
WHERE user_id = ?
  AND date >= date('now', '-30 days')  -- Past 30 days (matching signal window)
  AND amount < 0                        -- Only debits/spending
  AND merchant_name IS NOT NULL         -- Must have merchant name
GROUP BY merchant_name
HAVING COUNT(*) >= 3                    -- ≥3 transactions in window
   AND day_span <= 90                   -- Span ≤90 days (matching SubscriptionDetector)
ORDER BY avg_amount DESC
```

### Key Changes

1. ✅ **Removed hardcoded merchant filter** - Now finds ALL recurring merchants (matching detector)
2. ✅ **Uses 30-day window** - Same as the signal computation (matching detector)
3. ✅ **Same span logic** - Checks if first-to-last span is ≤90 days (matching detector)
4. ✅ **Only negative transactions** - Debits/spending only (matching detector)

### Fix 2: Disabled Caching for Profile Endpoint

Updated `get_user_profile` method to **always compute fresh signals** by default:
- Changed default `use_cache` parameter from `True` to `False`
- Profile endpoint now always computes fresh signals when called
- Both endpoints now use the same fresh data source

**Before:**
```python
signals_30d = self.aggregator.compute_signals(user_id, '30d', use_cache=True)  # Used cached data
```

**After:**
```python
signals_30d = self.aggregator.compute_signals(user_id, '30d', use_cache=False)  # Always fresh
```

### Fix 3: Aligned Date Range and Pending Transaction Filtering ⚠️ CRITICAL

Updated subscription endpoint to use **exact same date calculations** as TimeWindowPartitioner:
- Calculate dates exactly like `get_30_day_window()`: `[today-30, today-1]`
- Added `pending = 0` filter to exclude pending transactions
- Both endpoints now query the exact same transaction set

**Before:**
```python
cutoff_30_days = date.today() - timedelta(days=30)
# Query: date >= cutoff_30_days (included today and pending transactions)
```

**After:**
```python
end_date = TODAY - timedelta(days=1)      # Exclude today
start_date = end_date - timedelta(days=29)  # 30 days total
# Query: date >= start_date AND date <= end_date AND pending = 0
```

## Result

Both views now show **the same subscription count** because:
1. They use **identical query logic** (same merchant detection, same time windows)
2. They use **fresh data** (no caching discrepancy)
3. They use **identical date ranges** `[today-30, today-1]` (exclude today)
4. They both **exclude pending transactions** (`pending = 0`)
5. Both compute from the exact same transaction set with the same rules

- Behavioral Insights: "You have 5 recurring subscriptions" → Uses fresh SubscriptionDetector
- Active Subscriptions: Shows 5 subscription cards → Uses matching API logic with fresh data and exact date filtering

## Files Changed

1. **`spendsense/api/data_routes.py`** - Updated `/data/subscriptions/{user_id}` endpoint
   - **Fix 1**: Removed hardcoded merchant filter
   - **Fix 1**: Aligned query logic with SubscriptionDetector
   - **Fix 3**: Imported `TODAY` from config
   - **Fix 3**: Calculate dates exactly like `TimeWindowPartitioner.get_30_day_window()`
   - **Fix 3**: Added `pending = 0` filter to exclude pending transactions
   - **Fix 3**: Use both start_date and end_date in WHERE clause
   
2. **`spendsense/operator/review.py`** - Updated `get_user_profile` method
   - **Fix 2**: Added `use_cache` parameter (default: `False`)
   - **Fix 2**: Changed default to always compute fresh signals

## Testing

To verify the fix:

1. Start the API server: `python run.py --start`
2. Open the web UI: `http://localhost:8000`
3. Load a user ID (e.g., `user_001`)
4. Compare:
   - **Behavioral Insights** section: "You have X recurring subscriptions"
   - **Active Subscriptions** section: Should show X subscription cards
5. The counts should now match!

## Notes

- The fix maintains the 30-day signal window for consistency with existing behavioral insights
- All recurring merchants are now shown (not just known subscription services like Netflix)
- This may include merchants like grocery stores or coffee shops if visited ≥3 times in 30 days
- The SubscriptionDetector was the source of truth - the API endpoint now aligns with it
- **Performance**: Computing fresh signals on every request is slightly slower, but ensures consistency
- **Caching**: If performance becomes an issue, consider a shorter cache TTL (e.g., 1 hour) instead of disabling caching entirely
- **Operator Dashboard**: Other uses of `get_user_profile` (like operator dashboard) can still use caching by passing `use_cache=True` if needed
- **Critical**: The date range mismatch (including/excluding today and pending transactions) was likely the main cause of the 1-subscription difference you observed
- **Today's transactions**: By design, both views now exclude today's transactions to avoid counting incomplete data

