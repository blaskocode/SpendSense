# Data Generator Improvement Recommendations

## Critical Missing Fields

### 1. **transaction_id** (REQUIRED)
Your transactions are missing the `transaction_id` field, which is a PRIMARY KEY in the database schema.

**Fix:**
```python
def generate_transactions(user_id, accounts):
    transactions = []
    # ... existing code ...
    
    transactions.append({
        "transaction_id": str(uuid.uuid4()),  # ADD THIS
        "user_id": user_id,
        "account_id": checking_acc["account_id"],
        # ... rest of fields
    })
```

### 2. **merchant_entity_id** (Recommended)
The schema supports this field for merchant identification.

**Fix:**
```python
"merchant_entity_id": str(uuid.uuid4()) if merchant_name else None,
```

### 3. **Account Type Structure**
Your accounts use `type` and `subtype` as separate fields, but SpendSense expects:
- `type`: 'depository' or 'credit'
- `subtype`: 'checking', 'savings', 'credit_card', 'hsa', 'money_market'

**Fix:**
```python
def generate_account(user_id):
    accounts = []
    
    # Checking account
    accounts.append({
        "user_id": user_id,
        "account_id": str(uuid.uuid4()),
        "type": "depository",  # Not "checking"
        "subtype": "checking",  # This is the subtype
        "balance_available": balance,
        "balance_current": balance,
        "balance_limit": None,
        "iso_currency_code": "USD",
    })
```

## Missing Account Types

### 4. **Credit Card Accounts**
SpendSense needs credit card accounts for credit utilization signals. Currently missing.

**Add:**
```python
# 60% chance of credit card
if random.random() < 0.6:
    credit_limit = random.uniform(monthly_income * 2, monthly_income * 10)
    balance = random.uniform(0, credit_limit * random.uniform(0.1, 0.8))
    accounts.append({
        "user_id": user_id,
        "account_id": str(uuid.uuid4()),
        "type": "credit",
        "subtype": "credit_card",
        "balance_available": credit_limit - balance,
        "balance_current": balance,
        "balance_limit": credit_limit,
        "iso_currency_code": "USD",
    })
```

### 5. **HSA and Money Market Accounts**
Optional but realistic account types.

**Add:**
```python
# 15% chance of HSA
if random.random() < 0.15:
    hsa_balance = random.uniform(1000, monthly_income * 3)
    accounts.append({
        "user_id": user_id,
        "account_id": str(uuid.uuid4()),
        "type": "depository",
        "subtype": "hsa",
        "balance_available": hsa_balance,
        "balance_current": hsa_balance,
        "balance_limit": None,
        "iso_currency_code": "USD",
    })
```

## Missing Data Structures

### 6. **Liabilities Table**
Credit cards need corresponding liability records with APR, minimum payments, etc.

**Add:**
```python
def generate_liabilities(accounts, user_id):
    """Generate liabilities for credit card accounts"""
    liabilities = []
    
    for account in accounts:
        if account['type'] == 'credit' and account['subtype'] == 'credit_card':
            apr = random.uniform(12.0, 28.0)
            min_payment = max(account['balance_current'] * 0.02, 25.0)
            next_due = datetime.date.today() + datetime.timedelta(days=random.randint(1, 30))
            is_overdue = random.random() < 0.1  # 10% chance
            
            liabilities.append({
                "liability_id": str(uuid.uuid4()),
                "account_id": account["account_id"],
                "type": "credit_card",
                "apr": round(apr, 2),
                "minimum_payment": round(min_payment, 2),
                "last_payment": round(min_payment, 2) if random.random() < 0.8 else None,
                "is_overdue": is_overdue,
                "next_payment_due": next_due.isoformat(),
                "last_statement_balance": round(account['balance_current'], 2),
            })
    
    return liabilities
```

### 7. **Users Table**
You're generating accounts and transactions but not user records.

**Add:**
```python
def generate_users(num_users):
    """Generate user records"""
    users = []
    start_date = START_DATE
    
    for i in range(num_users):
        user_id = str(uuid.uuid4())
        users.append({
            "user_id": user_id,
            "created_at": start_date.isoformat(),
            "consent_status": False,  # Default to False
            "consent_timestamp": None,
            "last_updated": datetime.date.today().isoformat(),
        })
    
    return users
```

## Data Quality Issues

### 8. **Subscription Duplicate Prevention**
Your fixed expenses can create duplicates if the same payment occurs multiple times in the same month.

**Fix:**
```python
# Track which months we've processed each payment
payment_months = set()

for name, cat, low, high, detail in FIXED_EXPENSES:
    if random.random() < 0.8:
        monthly_day = random.randint(1, 28)
        current_month = start.replace(day=1)
        
        while current_month < end:
            # Check if we've already processed this payment this month
            month_key = (current_month.year, current_month.month, name)
            if month_key not in payment_months:
                payment_date = current_month.replace(day=min(monthly_day, 28))
                
                if start <= payment_date <= end:
                    transactions.append({
                        # ... transaction data
                    })
                    payment_months.add(month_key)
            
            # Move to next month
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)
```

### 9. **Account-Appropriate Transactions**
HSA accounts should only have healthcare transactions. Your generator doesn't enforce this.

**Fix:**
```python
# When generating transactions, check account type
if account['subtype'] == 'hsa':
    # Only healthcare transactions
    category = random.choice(['Healthcare', 'Medical', 'Pharmacy'])
    merchant_name = random.choice(['Pharmacy', 'Doctor', 'Hospital', 'Medical Clinic'])
elif account['subtype'] == 'credit_card':
    # Credit card transactions
    # ... credit card spending logic
```

### 10. **Realistic Balance Tracking**
Account balances should update based on transactions, not just be random starting values.

**Fix:**
```python
def generate_transactions_with_balance_tracking(user_id, accounts):
    """Generate transactions and update account balances"""
    transactions = []
    
    # Initialize balance tracking
    balances = {acc['account_id']: acc['balance_current'] for acc in accounts}
    
    # ... generate transactions ...
    
    # After each transaction, update balance
    for tx in transactions:
        account_id = tx['account_id']
        balances[account_id] += tx['amount']  # amount is already negative for expenses
    
    # Update account balances
    for account in accounts:
        account['balance_current'] = balances[account['account_id']]
        account['balance_available'] = balances[account['account_id']]
        if account['type'] == 'credit':
            account['balance_available'] = account['balance_limit'] - balances[account['account_id']]
    
    return transactions
```

## Missing Transaction Types

### 11. **Credit Card Transactions**
You generate checking/savings transactions but no credit card spending.

**Add:**
```python
# Credit card spending
credit_card_acc = [a for a in accounts if a.get('subtype') == 'credit_card']
if credit_card_acc:
    credit_card = credit_card_acc[0]
    
    # Generate credit card purchases
    for _ in range(random.randint(20, 60)):
        tx_date = random_date(start, end)
        amount = -random.uniform(10, 300)
        
        transactions.append({
            "transaction_id": str(uuid.uuid4()),
            "user_id": user_id,
            "account_id": credit_card["account_id"],
            "date": tx_date.isoformat(),
            "amount": round(amount, 2),
            "merchant_name": random.choice(['Merchant', 'Store', 'Restaurant']),
            "merchant_entity_id": str(uuid.uuid4()),
            "payment_channel": "card",
            "personal_finance_category": random.choice([
                "EXPENSE_FOOD_AND_DRINK",
                "EXPENSE_SHOPPING",
                "EXPENSE_ENTERTAINMENT",
            ]),
            "pending": False
        })
    
    # Credit card payments (monthly)
    current_date = start
    while current_date < end:
        if current_date.day in range(23, 28):  # Payment window
            if random.random() < 0.8:  # 80% chance of payment
                payment_amount = min(
                    balances[credit_card["account_id"]] * random.uniform(0.1, 1.0),
                    credit_card['balance_limit']
                )
                transactions.append({
                    "transaction_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "account_id": credit_card["account_id"],
                    "date": current_date.isoformat(),
                    "amount": round(payment_amount, 2),  # Positive = payment
                    "merchant_name": "Credit Card Payment",
                    "merchant_entity_id": None,
                    "payment_channel": "ach",
                    "personal_finance_category": "TRANSFER_PAYMENT",
                    "pending": False
                })
        current_date += datetime.timedelta(days=1)
```

## Category Field Names

### 12. **Category Field Consistency**
Your code uses `personal_finance_category` but SpendSense schema uses `category_primary` and `category_detailed`.

**Fix:**
```python
# Change from:
"personal_finance_category": "INCOME_PAYROLL"

# To:
"category_primary": "Transfer",
"category_detailed": "Payroll"
```

## Persona-Based Generation

### 13. **Persona Integration** (Advanced)
For realistic data that matches SpendSense's persona system, consider integrating persona profiles.

**Recommendation:**
- Use the existing `persona_profiles.py` system
- Generate users that match persona characteristics
- High Utilization: High credit utilization, minimum payments
- Variable Income: Irregular payroll dates
- Subscription-Heavy: Many recurring subscriptions
- Savings Builder: Regular savings transfers
- Credit Builder: No credit cards or low utilization

## Additional Improvements

### 14. **Date Handling**
Use proper date objects instead of strings until final export.

**Fix:**
```python
from datetime import date, timedelta

# Use date objects internally
tx_date = random_date(start, end)

# Convert to string only when creating final dict
"date": tx_date.isoformat()
```

### 15. **Validation**
Add validation before exporting to catch errors early.

**Fix:**
```python
from spendsense.ingest.validator import DataValidator

# Before exporting
DataValidator.validate_batch(users, 'user')
DataValidator.validate_batch(accounts, 'account')
DataValidator.validate_batch(transactions, 'transaction')
DataValidator.validate_batch(liabilities, 'liability')
```

### 16. **Income Variability**
For Variable Income Budgeter persona, add irregular income patterns.

**Fix:**
```python
# Variable income pattern
if persona == "Variable Income Budgeter":
    # Irregular paychecks - gaps of 30-60 days
    next_pay = start
    while next_pay < end:
        pay_amount = income_base * random.uniform(0.7, 1.3)  # More variability
        transactions.append({
            # ... payroll transaction
        })
        # Next paycheck in 30-60 days (irregular)
        next_pay += datetime.timedelta(days=random.randint(30, 60))
```

### 17. **Subscription Tracking**
Track subscriptions separately to prevent duplicates and enable realistic patterns.

**Fix:**
```python
# Track active subscriptions
active_subscriptions = []

# Add subscription
subscription = {
    'merchant_name': 'Netflix',
    'amount': 14.99,
    'day_of_month': 15,
    'start_date': start,
    'active': True
}
active_subscriptions.append(subscription)

# Generate subscription payments
for sub in active_subscriptions:
    if not sub['active']:
        continue
    
    current_month = start.replace(day=1)
    while current_month < end:
        payment_date = current_month.replace(day=min(sub['day_of_month'], 28))
        
        if start <= payment_date <= end:
            # Check if we've already created this payment
            month_key = (payment_date.year, payment_date.month, sub['merchant_name'])
            if month_key not in payment_months:
                transactions.append({
                    # ... subscription payment
                })
                payment_months.add(month_key)
        
        # Move to next month
        if current_month.month == 12:
            current_month = current_month.replace(year=current_month.year + 1, month=1)
        else:
            current_month = current_month.replace(month=current_month.month + 1)
```

## Summary of Critical Fixes

1. ✅ Add `transaction_id` to all transactions
2. ✅ Fix account `type`/`subtype` structure
3. ✅ Add credit card accounts
4. ✅ Add liabilities generation
5. ✅ Add users table generation
6. ✅ Fix category field names (`category_primary`, `category_detailed`)
7. ✅ Add credit card transactions
8. ✅ Prevent subscription duplicates
9. ✅ Add account-appropriate transaction routing
10. ✅ Add balance tracking over time

## Integration with SpendSense

To integrate your generator with SpendSense:

1. **Use SpendSense's DataImporter:**
```python
from spendsense.ingest.importer import DataImporter

importer = DataImporter()
importer.import_synthetic_data(use_profiles=False)  # Use your generator
```

2. **Or modify your generator to match SpendSense's interface:**
```python
# Your generator should return:
# - List[User] (dataclass or dict)
# - List[Account] (dataclass or dict)
# - List[Transaction] (dataclass or dict)
# - List[Liability] (dataclass or dict)
```

3. **Use SpendSense's validation:**
```python
from spendsense.ingest.validator import DataValidator

# Validate before importing
DataValidator.validate_batch(users, 'user')
DataValidator.validate_batch(accounts, 'account')
DataValidator.validate_batch(transactions, 'transaction')
DataValidator.validate_batch(liabilities, 'liability')
```

