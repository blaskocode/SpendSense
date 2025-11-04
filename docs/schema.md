# SpendSense Database Schema

This document describes the database schemas used in SpendSense, with examples.

## SQLite Schema

SpendSense uses SQLite for relational data storage. All tables use rowid-based primary keys with TEXT identifiers for business logic.

### Users Table

**Purpose:** Stores user accounts and consent status

```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    consent_status BOOLEAN DEFAULT FALSE,
    consent_timestamp TIMESTAMP,
    last_updated TIMESTAMP NOT NULL
)
```

**Example:**
```python
{
    'user_id': 'user_001',
    'created_at': '2024-01-15T10:00:00',
    'consent_status': True,
    'consent_timestamp': '2024-01-15T10:05:00',
    'last_updated': '2024-01-20T14:30:00'
}
```

### Accounts Table

**Purpose:** Stores financial accounts (checking, savings, credit cards, etc.)

```sql
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    subtype TEXT,
    balance_available REAL,
    balance_current REAL,
    balance_limit REAL,
    iso_currency_code TEXT DEFAULT 'USD',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

**Example:**
```python
{
    'account_id': 'acc_checking_001',
    'user_id': 'user_001',
    'type': 'checking',
    'subtype': 'checking',
    'balance_available': 1250.50,
    'balance_current': 1250.50,
    'balance_limit': None,
    'iso_currency_code': 'USD'
}
```

### Transactions Table

**Purpose:** Stores individual transactions

```sql
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    date DATE NOT NULL,
    amount REAL NOT NULL,
    merchant_name TEXT,
    merchant_entity_id TEXT,
    payment_channel TEXT,
    category_primary TEXT,
    category_detailed TEXT,
    pending BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
)
```

**Example:**
```python
{
    'transaction_id': 'txn_abc123',
    'account_id': 'acc_checking_001',
    'date': '2024-01-20',
    'amount': -29.99,
    'merchant_name': 'Netflix',
    'merchant_entity_id': 'netflix_001',
    'payment_channel': 'card',
    'category_primary': 'entertainment',
    'category_detailed': 'subscriptions',
    'pending': False
}
```

### Liabilities Table

**Purpose:** Stores credit card balances, loans, and other liabilities

```sql
CREATE TABLE liabilities (
    liability_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    type TEXT NOT NULL,
    apr REAL,
    minimum_payment REAL,
    current_balance REAL,
    statement_balance REAL,
    last_payment_date DATE,
    next_payment_date DATE,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
)
```

**Example:**
```python
{
    'liability_id': 'liab_cc_001',
    'account_id': 'acc_credit_001',
    'type': 'credit_card',
    'apr': 18.99,
    'minimum_payment': 25.00,
    'current_balance': 1250.00,
    'statement_balance': 1250.00,
    'last_payment_date': '2024-01-15',
    'next_payment_date': '2024-02-15'
}
```

### Signals Table

**Purpose:** Stores computed behavioral signals

```sql
CREATE TABLE signals (
    signal_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    window_type TEXT NOT NULL,
    subscriptions_count INTEGER DEFAULT 0,
    subscriptions_monthly_spend REAL DEFAULT 0,
    subscriptions_share_of_spend REAL DEFAULT 0,
    savings_growth_rate REAL DEFAULT 0,
    net_inflow REAL DEFAULT 0,
    emergency_fund_months REAL DEFAULT 0,
    credit_utilization REAL DEFAULT 0,
    interest_charges REAL DEFAULT 0,
    min_payment_only BOOLEAN DEFAULT FALSE,
    overdue BOOLEAN DEFAULT FALSE,
    payroll_detected BOOLEAN DEFAULT FALSE,
    payroll_frequency_days INTEGER,
    income_variability REAL DEFAULT 0,
    income_buffer_months REAL DEFAULT 0,
    computed_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

**Example:**
```python
{
    'signal_id': 'sig_001_30d',
    'user_id': 'user_001',
    'window_type': '30d',
    'subscriptions_count': 3,
    'subscriptions_monthly_spend': 75.00,
    'subscriptions_share_of_spend': 12.5,
    'savings_growth_rate': 2.5,
    'net_inflow': 200.00,
    'emergency_fund_months': 3.0,
    'credit_utilization': 25.0,
    'interest_charges': 0.0,
    'min_payment_only': False,
    'overdue': False,
    'payroll_detected': True,
    'payroll_frequency_days': 14,
    'income_variability': 0.1,
    'income_buffer_months': 2.5,
    'computed_at': '2024-01-20T12:00:00'
}
```

### Personas Table

**Purpose:** Stores assigned personas with decision traces

```sql
CREATE TABLE personas (
    persona_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    persona_name TEXT NOT NULL,
    priority_level INTEGER NOT NULL,
    signal_strength REAL NOT NULL,
    decision_trace TEXT,
    assigned_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

**Example:**
```python
{
    'persona_id': 'persona_001',
    'user_id': 'user_001',
    'persona_name': 'Credit Builder',
    'priority_level': 3,
    'signal_strength': 1.0,
    'decision_trace': '{"all_matched_personas": ["Credit Builder", "Savings Builder"], "reason": "No active credit usage"}',
    'assigned_at': '2024-01-20T12:00:00'
}
```

### Recommendations Table

**Purpose:** Stores generated recommendations

```sql
CREATE TABLE recommendations (
    recommendation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL,
    rationale TEXT NOT NULL,
    persona_name TEXT NOT NULL,
    operator_status TEXT DEFAULT 'pending',
    generated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

**Example:**
```python
{
    'recommendation_id': 'rec_001',
    'user_id': 'user_001',
    'title': 'Credit 101: How Credit Works',
    'description': 'Understanding how credit works is essential...',
    'type': 'education',
    'rationale': 'Because you have no active credit usage, this content will help you build credit responsibly.',
    'persona_name': 'Credit Builder',
    'operator_status': 'approved',
    'generated_at': '2024-01-20T12:00:00'
}
```

### Feedback Table

**Purpose:** Stores user feedback on recommendations

```sql
CREATE TABLE feedback (
    feedback_id TEXT PRIMARY KEY,
    recommendation_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    thumbs_up BOOLEAN,
    helped_me BOOLEAN,
    applied_this BOOLEAN,
    free_text TEXT,
    submitted_at TIMESTAMP NOT NULL,
    FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

**Example:**
```python
{
    'feedback_id': 'fb_001',
    'recommendation_id': 'rec_001',
    'user_id': 'user_001',
    'thumbs_up': True,
    'helped_me': True,
    'applied_this': False,
    'free_text': 'Very helpful!',
    'submitted_at': '2024-01-21T10:00:00'
}
```

## Parquet Schema

SpendSense also exports analytical data to Parquet format for efficient querying and analysis.

### Transaction Parquet

**Columns:** Same as transactions table, optimized for analytics

### Account Parquet

**Columns:** Same as accounts table, optimized for analytics

## Indexes

For performance, the following indexes are created:

- `users(user_id)` - Primary key
- `accounts(user_id)` - Foreign key lookup
- `transactions(account_id, date)` - Transaction queries
- `signals(user_id, window_type)` - Signal lookups
- `personas(user_id)` - Persona lookups
- `recommendations(user_id, operator_status)` - Recommendation queries

## Data Types

- **TEXT:** String identifiers and text fields
- **REAL:** Floating-point numbers (amounts, percentages)
- **INTEGER:** Whole numbers (counts, days)
- **BOOLEAN:** True/false values
- **TIMESTAMP:** ISO 8601 datetime strings
- **DATE:** ISO 8601 date strings

## Relationships

```
users (1) ──< (many) accounts
accounts (1) ──< (many) transactions
accounts (1) ──< (many) liabilities
users (1) ──< (many) signals
users (1) ──< (many) personas
users (1) ──< (many) recommendations
recommendations (1) ──< (many) feedback
```

