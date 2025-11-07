# Improved Data Generator - Usage Guide

## Overview

The improved data generator has been integrated into SpendSense as a new option alongside the existing profile-based and Capital One generators. It includes all the fixes and improvements recommended for better data quality.

## Features

✅ **Complete Schema Compliance**
- All required fields (`transaction_id`, `merchant_entity_id`, etc.)
- Proper account type structure (`type`/`subtype`)
- Correct category field names (`category_primary`/`category_detailed`)

✅ **Comprehensive Account Types**
- Checking accounts (always)
- Savings accounts (80% chance)
- Credit cards (60% chance) with proper utilization
- Money market accounts (20% chance)
- HSA accounts (15% chance) with healthcare-only transactions

✅ **Realistic Transaction Patterns**
- Payroll deposits (monthly, semi-monthly, biweekly)
- Fixed expenses (rent, utilities, etc.) with duplicate prevention
- Subscription payments (2-8 per user) with proper tracking
- Variable expenses (groceries, gas, restaurants)
- Credit card spending and payments
- Savings transfers
- HSA healthcare transactions

✅ **Balance Tracking**
- Account balances update based on transaction history
- Credit card available credit calculated correctly
- Realistic balance progression over time

✅ **Liabilities Generation**
- Credit card liabilities with APR based on utilization
- Minimum payment calculations
- Overdue status tracking
- Payment due dates

## Usage

### Command Line

```bash
# Use improved generator
python run.py --setup --use-improved

# Use profile-based generator (default)
python run.py --setup

# Use Capital One generator
python run.py --setup --no-profiles
```

### Python API

```python
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.storage.parquet_handler import ParquetHandler
from spendsense.ingest.importer import DataImporter

# Initialize
db_manager = SQLiteManager()
db_manager.create_schema()
parquet_handler = ParquetHandler()
importer = DataImporter(db_manager, parquet_handler)

# Use improved generator
importer.import_synthetic_data(
    num_users=100,
    seed=42,
    use_improved=True
)

# Or use profile-based (default)
importer.import_synthetic_data(
    num_users=100,
    seed=42,
    use_profiles=True
)

# Or use Capital One generator
importer.import_synthetic_data(
    num_users=100,
    seed=42,
    use_profiles=False
)
```

## Generator Comparison

| Feature | Improved Generator | Profile-Based | Capital One |
|---------|-------------------|---------------|-------------|
| Schema Compliance | ✅ Full | ✅ Full | ✅ Full |
| Account Types | ✅ All 5 types | ✅ All 5 types | ✅ All 5 types |
| Credit Cards | ✅ Yes | ✅ Yes | ✅ Yes |
| Liabilities | ✅ Yes | ✅ Yes | ✅ Yes |
| Balance Tracking | ✅ Yes | ✅ Yes | ⚠️ Limited |
| Duplicate Prevention | ✅ Yes | ✅ Yes | ⚠️ Limited |
| Persona-Based | ❌ No | ✅ Yes | ❌ No |
| Subscription Tracking | ✅ Yes | ✅ Yes | ⚠️ Limited |
| HSA Healthcare Only | ✅ Yes | ✅ Yes | ⚠️ Limited |
| Realistic Patterns | ✅ Good | ✅ Excellent | ✅ Good |

## Key Improvements Over Original Generator

1. **Missing Fields Fixed**
   - Added `transaction_id` to all transactions
   - Added `merchant_entity_id` for merchant tracking
   - Fixed account `type`/`subtype` structure

2. **Missing Account Types**
   - Added credit card accounts (60% chance)
   - Added HSA accounts (15% chance)
   - Added money market accounts (20% chance)

3. **Missing Data Structures**
   - Added liabilities generation for credit cards
   - Added users table generation

4. **Data Quality**
   - Subscription duplicate prevention
   - Account-appropriate transaction routing (HSA only healthcare)
   - Balance tracking over time
   - Credit card payment logic

5. **Category Fields**
   - Fixed to use `category_primary` and `category_detailed`
   - Proper category mapping

## Example Output

The improved generator creates:
- **100 users** (configurable)
- **~230 accounts** (checking, savings, credit, HSA, money market)
- **~10,000+ transactions** (realistic patterns)
- **~60 liabilities** (credit card accounts)

## Integration with SpendSense

The improved generator is fully integrated with:
- ✅ Data validation (`DataValidator`)
- ✅ SQLite import (`SQLiteManager`)
- ✅ Parquet export (`ParquetHandler`)
- ✅ All SpendSense dataclasses (`User`, `Account`, `Transaction`, `Liability`)

## Testing

To test the improved generator:

```bash
# Generate data with improved generator
python run.py --setup --use-improved

# Start API server
python run.py --start

# Access user dashboard
# Open http://localhost:8000 in browser
```

## Next Steps

The improved generator is ready to use! You can:
1. Generate data with `--use-improved` flag
2. Test the generated data through the API
3. Compare results with profile-based generator
4. Use it as a fallback or alternative to persona-based generation

## Notes

- The improved generator does NOT use persona profiles (unlike profile-based generator)
- It generates more generic but comprehensive data
- Good for testing and development
- Profile-based generator is still recommended for realistic persona-driven data

