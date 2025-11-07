"""Improved synthetic data generator with comprehensive features"""

import random
import uuid
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
import pytz

from ..utils.config import NUM_USERS, SEED, DAYS_OF_HISTORY, TODAY
from ..utils.logger import setup_logger
from .data_generator import User, Account, Transaction, Liability

logger = setup_logger(__name__)

# Set seed for reproducibility
random.seed(SEED)

# --- CONFIGURABLE PARAMETERS ---
START_DATE = TODAY - timedelta(days=DAYS_OF_HISTORY)
END_DATE = TODAY - timedelta(days=1)

# --- CATEGORY DEFINITIONS ---
INCOME_SOURCES = [
    {"name": "Payroll", "merchant": "Employer Payroll", "category_primary": "Transfer", "category_detailed": "Payroll"},
    {"name": "Freelance", "merchant": "Upwork", "category_primary": "Transfer", "category_detailed": "Freelance"},
    {"name": "Investment", "merchant": "Brokerage Deposit", "category_primary": "Transfer", "category_detailed": "Investment"},
]

FIXED_EXPENSES = [
    ("Rent Payment", "Bills", 1200, 2500, "Rent"),
    ("Mortgage Payment", "Bills", 1800, 4000, "Mortgage"),
    ("Electric Company", "Bills", 100, 300, "Utilities"),
    ("Internet Provider", "Bills", 50, 120, "Internet"),
    ("Phone Bill", "Bills", 50, 150, "Phone"),
    ("Car Payment", "Bills", 250, 700, "Auto Loan"),
    ("Insurance", "Bills", 100, 400, "Insurance"),
    # Note: Gym Membership and Streaming Service moved to SUBSCRIPTION_MERCHANTS to avoid duplicates
]

VARIABLE_EXPENSES = [
    ("Groceries", "Food and Drink", 30, 180, "Groceries"),
    ("Dining Out", "Food and Drink", 10, 120, "Restaurants"),
    ("Gas Station", "Transportation", 20, 90, "Gas Stations"),
    ("Retail Shopping", "Shops", 15, 300, "Retail"),
    ("Health & Wellness", "Healthcare", 10, 150, "Health"),
    ("Entertainment", "Entertainment", 10, 150, "Entertainment"),
    ("Travel", "Travel", 50, 500, "Travel"),
    ("Donations", "Charity", 10, 200, "Donation"),
    ("Pet Care", "Pet", 20, 100, "Pet"),
]

# Subscription merchants with realistic amounts
SUBSCRIPTION_MERCHANTS = [
    ("Netflix", 14.99, "Entertainment", "Subscription"),
    ("Spotify", 9.99, "Entertainment", "Subscription"),
    ("Amazon Prime", 14.99, "Entertainment", "Subscription"),
    ("Disney+", 10.99, "Entertainment", "Subscription"),
    ("Hulu", 12.99, "Entertainment", "Subscription"),
    ("Apple Music", 9.99, "Entertainment", "Subscription"),
    ("Gym Membership", 50.00, "Entertainment", "Subscription"),
    ("Software Subscription", 29.99, "Entertainment", "Subscription"),
    ("Newspaper", 9.99, "Entertainment", "Subscription"),
]

# Healthcare merchants for HSA accounts
HEALTHCARE_MERCHANTS = [
    ("Pharmacy", "Healthcare", "Pharmacy"),
    ("Doctor", "Healthcare", "Medical"),
    ("Hospital", "Healthcare", "Medical"),
    ("Dental Clinic", "Healthcare", "Dental"),
    ("Medical Clinic", "Healthcare", "Medical"),
]


class ImprovedDataGenerator:
    """Improved synthetic data generator with comprehensive features"""
    
    def __init__(self, num_users: int = NUM_USERS, seed: int = SEED):
        self.num_users = num_users
        self.seed = seed
        random.seed(seed)
        self.start_date = START_DATE
        self.end_date = END_DATE
        
    def generate_all(self) -> Tuple[List[User], List[Account], List[Transaction], List[Liability]]:
        """Generate all synthetic data"""
        logger.info(f"Generating improved synthetic data for {self.num_users} users")
        
        users = []
        accounts = []
        transactions = []
        liabilities = []
        
        for i in range(self.num_users):
            user_id = f"user_{i+1:03d}"
            
            # Generate user
            user = User(
                user_id=user_id,
                created_at=self.start_date,
                consent_status=False,
                consent_timestamp=None,
                last_updated=self.end_date
            )
            users.append(user)
            
            # Generate accounts and transactions for this user
            user_accounts, user_transactions, user_liabilities = self._generate_user_data(user_id)
            accounts.extend(user_accounts)
            transactions.extend(user_transactions)
            liabilities.extend(user_liabilities)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Generated data for {i+1}/{self.num_users} users")
        
        # Validate for duplicate recurring payments
        self._validate_no_duplicate_recurring_payments(transactions)
        
        logger.info(f"Generated {len(users)} users, {len(accounts)} accounts, "
                   f"{len(transactions)} transactions, {len(liabilities)} liabilities")
        
        return users, accounts, transactions, liabilities
    
    def _validate_no_duplicate_recurring_payments(self, transactions: List[Transaction]):
        """Validate that recurring payments (rent, subscriptions, etc.) only occur once per month"""
        # Track recurring payment merchants
        recurring_merchants = set()
        for exp in FIXED_EXPENSES:
            recurring_merchants.add(exp[0])  # Merchant name
        for sub in SUBSCRIPTION_MERCHANTS:
            recurring_merchants.add(sub[0])  # Merchant name
        
        # Group transactions by account, merchant, and month (more precise than user)
        # This catches duplicates even if they're on different accounts
        payment_tracking: Dict[Tuple[str, str, int, int], List[Transaction]] = {}
        
        for tx in transactions:
            if tx.merchant_name and tx.merchant_name in recurring_merchants:
                # Use account_id, merchant_name, year, month as key
                key = (tx.account_id, tx.merchant_name, tx.date.year, tx.date.month)
                if key not in payment_tracking:
                    payment_tracking[key] = []
                payment_tracking[key].append(tx)
        
        # Check for duplicates
        duplicates_found = []
        for key, txs in payment_tracking.items():
            if len(txs) > 1:
                duplicates_found.append((key, txs))
        
        if duplicates_found:
            logger.warning(f"Found {len(duplicates_found)} potential duplicate recurring payments:")
            for key, txs in duplicates_found[:5]:  # Show first 5 with details
                logger.warning(f"  {key[1]} appears {len(txs)} times in {key[2]}-{key[3]:02d} on account {key[0]}")
                # Show the dates of duplicates
                dates = sorted([tx.date for tx in txs])
                logger.warning(f"    Dates: {[str(d) for d in dates]}")
            if len(duplicates_found) > 5:
                logger.warning(f"  ... and {len(duplicates_found) - 5} more duplicates")
        else:
            logger.info("Validation passed: No duplicate recurring payments found")
    
    def _generate_user_data(self, user_id: str) -> Tuple[List[Account], List[Transaction], List[Liability]]:
        """Generate accounts, transactions, and liabilities for a single user"""
        # Select income level
        income_base = random.randint(2000, 8000)  # Monthly income
        monthly_income = income_base
        
        # Generate accounts
        accounts = self._generate_accounts(user_id, monthly_income)
        
        # Generate transactions with balance tracking
        transactions = []
        balances = {acc.account_id: acc.balance_current for acc in accounts}
        
        # Map accounts by subtype for easy lookup
        account_map = {acc.subtype: acc for acc in accounts}
        
        # Track all recurring merchants to prevent duplicates across fixed expenses and subscriptions
        recurring_merchants_used = set()
        
        # Generate payroll deposits
        pay_frequency = random.choice(["monthly", "semimonthly", "biweekly"])
        payroll_transactions = self._generate_payroll_deposits(
            user_id, account_map.get('checking'), monthly_income, pay_frequency, balances
        )
        transactions.extend(payroll_transactions)
        
        # Generate fixed expenses (rent, utilities, etc.)
        fixed_transactions, fixed_merchants = self._generate_fixed_expenses(
            user_id, account_map.get('checking'), balances, recurring_merchants_used
        )
        transactions.extend(fixed_transactions)
        recurring_merchants_used.update(fixed_merchants)
        
        # Generate subscriptions (excluding any that were already generated as fixed expenses)
        subscription_transactions = self._generate_subscriptions(
            user_id, accounts, balances, recurring_merchants_used
        )
        transactions.extend(subscription_transactions)
        
        # Generate variable expenses
        variable_transactions = self._generate_variable_expenses(
            user_id, accounts, balances
        )
        transactions.extend(variable_transactions)
        
        # Generate credit card transactions (if credit card exists)
        if 'credit_card' in account_map:
            credit_transactions = self._generate_credit_card_transactions(
                user_id, account_map['credit_card'], account_map.get('checking'), 
                monthly_income, balances
            )
            transactions.extend(credit_transactions)
        
        # Generate savings transfers
        if 'checking' in account_map and 'savings' in account_map:
            savings_transactions = self._generate_savings_transfers(
                user_id, account_map['checking'], account_map['savings'], balances
            )
            transactions.extend(savings_transactions)
        
        # Generate HSA transactions (if HSA exists)
        if 'hsa' in account_map:
            hsa_transactions = self._generate_hsa_transactions(
                user_id, account_map['hsa'], balances
            )
            transactions.extend(hsa_transactions)
        
        # Update account balances based on transactions
        self._update_account_balances(accounts, balances)
        
        # Generate liabilities
        liabilities = self._generate_liabilities(accounts, user_id)
        
        return accounts, transactions, liabilities
    
    def _generate_accounts(self, user_id: str, monthly_income: float) -> List[Account]:
        """Generate accounts for a user"""
        accounts = []
        
        # Always create a checking account
        checking_balance = random.uniform(500, monthly_income * 2)
        accounts.append(Account(
            account_id=f"{user_id}_checking",
            user_id=user_id,
            type='depository',
            subtype='checking',
            balance_available=checking_balance,
            balance_current=checking_balance
        ))
        
        # 80% chance of savings account
        if random.random() < 0.8:
            savings_balance = random.uniform(1000, monthly_income * 6)
            accounts.append(Account(
                account_id=f"{user_id}_savings",
                user_id=user_id,
                type='depository',
                subtype='savings',
                balance_available=savings_balance,
                balance_current=savings_balance
            ))
        
        # 60% chance of credit card
        if random.random() < 0.6:
            credit_limit = random.uniform(monthly_income * 2, monthly_income * 10)
            balance = random.uniform(0, credit_limit * random.uniform(0.1, 0.8))
            accounts.append(Account(
                account_id=f"{user_id}_credit",
                user_id=user_id,
                type='credit',
                subtype='credit_card',
                balance_available=credit_limit - balance,
                balance_current=balance,
                balance_limit=credit_limit
            ))
        
        # 20% chance of money market
        if random.random() < 0.2:
            mm_balance = random.uniform(5000, monthly_income * 12)
            accounts.append(Account(
                account_id=f"{user_id}_money_market",
                user_id=user_id,
                type='depository',
                subtype='money_market',
                balance_available=mm_balance,
                balance_current=mm_balance
            ))
        
        # 15% chance of HSA
        if random.random() < 0.15:
            hsa_balance = random.uniform(1000, monthly_income * 3)
            accounts.append(Account(
                account_id=f"{user_id}_hsa",
                user_id=user_id,
                type='depository',
                subtype='hsa',
                balance_available=hsa_balance,
                balance_current=hsa_balance
            ))
        
        return accounts
    
    def _generate_payroll_deposits(
        self, user_id: str, checking_account: Optional[Account], 
        monthly_income: float, frequency: str, balances: Dict[str, float]
    ) -> List[Transaction]:
        """Generate payroll deposits"""
        if not checking_account:
            return []
        
        transactions = []
        current_date = self.start_date
        
        if frequency == "monthly":
            amount = monthly_income
            while current_date <= self.end_date:
                if current_date.day == 1:
                    tx = self._create_transaction(
                        checking_account.account_id,
                        current_date,
                        amount,
                        merchant_name="Employer Payroll",
                        category_primary="Transfer",
                        category_detailed="Payroll",
                        payment_channel="ach"
                    )
                    transactions.append(tx)
                    balances[checking_account.account_id] += amount
                current_date += timedelta(days=1)
        
        elif frequency == "semimonthly":
            amount = monthly_income / 2
            while current_date <= self.end_date:
                if current_date.day in [1, 15]:
                    tx = self._create_transaction(
                        checking_account.account_id,
                        current_date,
                        amount,
                        merchant_name="Employer Payroll",
                        category_primary="Transfer",
                        category_detailed="Payroll",
                        payment_channel="ach"
                    )
                    transactions.append(tx)
                    balances[checking_account.account_id] += amount
                current_date += timedelta(days=1)
        
        else:  # biweekly
            amount = monthly_income * 26 / 12 / 2  # Approximate biweekly
            next_pay = self.start_date
            while next_pay <= self.end_date:
                tx = self._create_transaction(
                    checking_account.account_id,
                    next_pay,
                    amount,
                    merchant_name="Employer Payroll",
                    category_primary="Transfer",
                    category_detailed="Payroll",
                    payment_channel="ach"
                )
                transactions.append(tx)
                balances[checking_account.account_id] += amount
                next_pay += timedelta(days=14)
        
        return transactions
    
    def _generate_fixed_expenses(
        self, user_id: str, checking_account: Optional[Account], 
        balances: Dict[str, float], recurring_merchants_used: Set[str]
    ) -> Tuple[List[Transaction], Set[str]]:
        """Generate fixed monthly expenses (rent, utilities, etc.) - ONE per month per expense"""
        if not checking_account:
            return [], set()
        
        transactions = []
        payment_months: Set[Tuple[int, int, str]] = set()  # (year, month, merchant_name)
        merchants_generated = set()
        
        # Select which fixed expenses this user has (excluding any already used)
        user_expenses = [
            exp for exp in FIXED_EXPENSES 
            if exp[0] not in recurring_merchants_used  # Don't duplicate merchants
            and random.random() < 0.8  # 80% chance user has this expense
        ]
        
        # Assign a FIXED day of month for each expense (consistent across all months)
        # Most recurring payments should be on the 1st of the month
        expense_days = {}
        for name, cat, low, high, detail in user_expenses:
            if 'rent' in name.lower() or 'mortgage' in name.lower():
                expense_days[name] = 1  # Rent/mortgage always on 1st
            else:
                # Target ~99% of bills on 1st to achieve ~85% overall
                # (Set very high because actual results are much lower than probability suggests)
                if random.random() < 0.99:  # 99% on 1st
                    expense_days[name] = 1  # Almost all bills on 1st
                else:
                    expense_days[name] = random.randint(2, 5)  # Very rarely on 2nd-5th
        
        # Also store the amount for each expense (consistent across months)
        expense_amounts = {}
        for name, cat, low, high, detail in user_expenses:
            expense_amounts[name] = -random.uniform(low, high)
        
        current_month = self.start_date.replace(day=1)
        end_month = self.end_date.replace(day=1)
        
        while current_month <= end_month:
            for name, cat, low, high, detail in user_expenses:
                # CRITICAL: Check if we've already processed this payment this month
                month_key = (current_month.year, current_month.month, name)
                if month_key in payment_months:
                    continue  # Already processed - skip to prevent duplicate
                
                # Use the fixed day of month for this expense
                payment_day = expense_days[name]
                
                # Calculate payment date with proper date handling
                try:
                    payment_date = date(current_month.year, current_month.month, payment_day)
                except ValueError:
                    # Handle invalid dates (e.g., Feb 30) - if day was 1, use 1st, otherwise use last valid day
                    if payment_day == 1:
                        payment_date = date(current_month.year, current_month.month, 1)
                    else:
                        payment_date = date(current_month.year, current_month.month, 28)
                
                # Only create if date is within our range
                if self.start_date <= payment_date <= self.end_date:
                    # Use the fixed amount for this expense
                    amount = expense_amounts[name]
                    
                    tx = self._create_transaction(
                        checking_account.account_id,
                        payment_date,
                        amount,
                        merchant_name=name,
                        category_primary=cat,
                        category_detailed=detail,
                        payment_channel="online"
                    )
                    transactions.append(tx)
                    balances[checking_account.account_id] += amount
                    
                    # CRITICAL: Mark this payment as processed for this month
                    payment_months.add(month_key)
                    merchants_generated.add(name)
            
            # Move to next month
            if current_month.month == 12:
                current_month = date(current_month.year + 1, 1, 1)
            else:
                current_month = date(current_month.year, current_month.month + 1, 1)
        
        return transactions, merchants_generated
    
    def _generate_subscriptions(
        self, user_id: str, accounts: List[Account], balances: Dict[str, float],
        recurring_merchants_used: Set[str]
    ) -> List[Transaction]:
        """Generate subscription payments - ONE per month per subscription, with fixed day of month"""
        transactions = []
        # CRITICAL: Use account_id in the key to prevent duplicates across different accounts
        # But actually, we want to prevent duplicates per user, so use a simpler key
        payment_months: Set[Tuple[int, int, str]] = set()  # (year, month, merchant_name)
        
        # Select 2-8 subscriptions for this user (excluding any already used as fixed expenses)
        available_subscriptions = [
            sub for sub in SUBSCRIPTION_MERCHANTS 
            if sub[0] not in recurring_merchants_used  # Don't duplicate merchants
        ]
        
        if not available_subscriptions:
            return []
        
        num_subscriptions = random.randint(2, min(8, len(available_subscriptions)))
        user_subscriptions = random.sample(
            available_subscriptions, 
            num_subscriptions
        )
        
        # CRITICAL: Ensure no duplicate merchants in user_subscriptions
        # Use a dict to guarantee uniqueness by merchant name
        unique_subscriptions_dict = {}
        for sub in user_subscriptions:
            merchant_name = sub[0]
            if merchant_name not in unique_subscriptions_dict:
                unique_subscriptions_dict[merchant_name] = sub
            else:
                logger.warning(f"Duplicate merchant {merchant_name} found in user_subscriptions for {user_id} - keeping first occurrence")
        user_subscriptions = list(unique_subscriptions_dict.values())
        
        # Log subscription selection for debugging
        merchant_names = [sub[0] for sub in user_subscriptions]
        netflix_count = merchant_names.count('Netflix')
        if netflix_count > 1:
            logger.error(f"CRITICAL: Netflix appears {netflix_count} times in user_subscriptions for {user_id}! All merchants: {merchant_names}")
        
        if len(user_subscriptions) != len(unique_subscriptions_dict):
            logger.error(f"CRITICAL: user_subscriptions has duplicates for {user_id}! Original: {len(user_subscriptions)}, Unique: {len(unique_subscriptions_dict)}")
        
        # Choose account for subscriptions (prefer credit card if available)
        credit_account = next((acc for acc in accounts if acc.subtype == 'credit_card'), None)
        checking_account = next((acc for acc in accounts if acc.subtype == 'checking'), None)
        subscription_account = credit_account if credit_account else checking_account
        
        if not subscription_account:
            return []
        
        # CRITICAL: Assign a FIXED day of month for each subscription (consistent across all months)
        # Most subscriptions should be on the 1st, with some variation
        subscription_days = {}
        for merchant_name, amount, cat_primary, cat_detailed in user_subscriptions:
            # Target ~99% of subscriptions on 1st to achieve ~85% overall
            # (Set very high because subscriptions are getting much lower percentages than probability suggests)
            if random.random() < 0.99:  # 99% on 1st
                subscription_days[merchant_name] = 1  # Almost all subscriptions on 1st
            else:
                subscription_days[merchant_name] = random.randint(2, 10)  # Very rarely on 2nd-10th
        
        current_month = self.start_date.replace(day=1)
        end_month = self.end_date.replace(day=1)
        
        # Track transactions created per subscription for debugging
        transactions_per_subscription = {}
        
        while current_month <= end_month:
            for merchant_name, amount, cat_primary, cat_detailed in user_subscriptions:
                # CRITICAL: Check if we've already processed this subscription this month
                month_key = (current_month.year, current_month.month, merchant_name)
                
                if month_key in payment_months:
                    continue  # Already processed - skip to prevent duplicate
                
                # CRITICAL: Mark as processed IMMEDIATELY to prevent any duplicate generation
                # This must happen BEFORE creating the transaction to ensure no duplicates
                payment_months.add(month_key)
                
                # Use the FIXED day of month for this subscription
                payment_day = subscription_days[merchant_name]
                
                # Calculate payment date with proper date handling
                try:
                    payment_date = date(current_month.year, current_month.month, payment_day)
                except ValueError:
                    # Handle invalid dates (e.g., Feb 30) - if day was 1, use 1st, otherwise use last valid day
                    if payment_day == 1:
                        payment_date = date(current_month.year, current_month.month, 1)
                    else:
                        payment_date = date(current_month.year, current_month.month, 28)
                
                # Only create if date is within our range
                if self.start_date <= payment_date <= self.end_date:
                    # FINAL SAFEGUARD: Check if we've already created a transaction for this merchant on this date
                    # This prevents any edge cases where payment_months set might not work correctly
                    duplicate_found = False
                    duplicate_count = 0
                    for existing_tx in transactions:
                        if (existing_tx.merchant_name == merchant_name and 
                            existing_tx.date == payment_date and
                            existing_tx.account_id == subscription_account.account_id):
                            duplicate_count += 1
                            if user_id == 'user_001' and merchant_name == 'Netflix' and payment_date.day == 1:
                                logger.error(f"CRITICAL user_001: Found duplicate #{duplicate_count} for Netflix on {payment_date}! Existing tx: {existing_tx.transaction_id[:20]}...")
                            duplicate_found = True
                            break
                    
                    if duplicate_found:
                        continue
                    
                    if not duplicate_found:
                        tx = self._create_transaction(
                            subscription_account.account_id,
                            payment_date,
                            -amount,
                            merchant_name=merchant_name,
                            category_primary=cat_primary,
                            category_detailed=cat_detailed,
                            payment_channel="other"
                        )
                        transactions.append(tx)
                        balances[subscription_account.account_id] += -amount
                        
                        # Track for debugging (only count actual transactions created)
                        if merchant_name not in transactions_per_subscription:
                            transactions_per_subscription[merchant_name] = 0
                        transactions_per_subscription[merchant_name] += 1
            
            # Move to next month
            if current_month.month == 12:
                current_month = date(current_month.year + 1, 1, 1)
            else:
                current_month = date(current_month.year, current_month.month + 1, 1)
        
        # Debug: Log transaction counts per subscription
        for merchant_name, count in transactions_per_subscription.items():
            if count > 7:  # More than 7 months of data
                logger.warning(f"User {user_id}: {merchant_name} generated {count} transactions (expected ~7 for 7 months)")
        
        
        return transactions
    
    def _generate_variable_expenses(
        self, user_id: str, accounts: List[Account], balances: Dict[str, float]
    ) -> List[Transaction]:
        """Generate variable expenses (groceries, gas, etc.)"""
        transactions = []
        
        # Choose account (prefer checking, fallback to credit if available)
        checking_account = next((acc for acc in accounts if acc.subtype == 'checking'), None)
        credit_account = next((acc for acc in accounts if acc.subtype == 'credit_card'), None)
        spending_account = checking_account if checking_account else credit_account
        
        if not spending_account:
            return []
        
        # Generate 80-200 variable transactions
        num_transactions = random.randint(80, 200)
        
        for _ in range(num_transactions):
            name, cat, low, high, detail = random.choice(VARIABLE_EXPENSES)
            tx_date = self._random_date(self.start_date, self.end_date)
            amount = -random.uniform(low, high)
            
            tx = self._create_transaction(
                spending_account.account_id,
                tx_date,
                amount,
                merchant_name=name,
                category_primary=cat,
                category_detailed=detail,
                payment_channel=random.choice(["in store", "online"])
            )
            transactions.append(tx)
            balances[spending_account.account_id] += amount
        
        return transactions
    
    def _generate_credit_card_transactions(
        self, user_id: str, credit_account: Account, checking_account: Optional[Account],
        monthly_income: float, balances: Dict[str, float]
    ) -> List[Transaction]:
        """Generate credit card spending and payments"""
        transactions = []
        
        # Generate credit card purchases
        num_purchases = random.randint(20, 60)
        for _ in range(num_purchases):
            tx_date = self._random_date(self.start_date, self.end_date)
            amount = -random.uniform(10, 300)
            
            # Random category
            name, cat, _, _, detail = random.choice(VARIABLE_EXPENSES)
            
            tx = self._create_transaction(
                credit_account.account_id,
                tx_date,
                amount,
                merchant_name=name,
                category_primary=cat,
                category_detailed=detail,
                payment_channel="card"
            )
            transactions.append(tx)
            balances[credit_account.account_id] += amount
        
        # Generate credit card payments (monthly, around day 25)
        current_date = self.start_date
        while current_date <= self.end_date:
            if current_date.day in range(23, 28):  # Payment window
                if random.random() < 0.8:  # 80% chance of payment
                    # Payment amount (minimum payment or more)
                    current_balance = balances.get(credit_account.account_id, 0)
                    if current_balance > 0:
                        min_payment = max(current_balance * 0.02, 25.0)
                        payment_amount = min(
                            current_balance * random.uniform(0.1, 1.0),
                            credit_account.balance_limit or float('inf')
                        )
                        payment_amount = max(payment_amount, min_payment)
                        
                        tx = self._create_transaction(
                            credit_account.account_id,
                            current_date,
                            payment_amount,  # Positive = payment
                            merchant_name="Credit Card Payment",
                            category_primary="Transfer",
                            category_detailed="Payment",
                            payment_channel="ach"
                        )
                        transactions.append(tx)
                        balances[credit_account.account_id] += payment_amount
                        
                        # Corresponding debit from checking (if available)
                        if checking_account:
                            debit_tx = self._create_transaction(
                                checking_account.account_id,
                                current_date,
                                -payment_amount,
                                merchant_name="Credit Card Payment",
                                category_primary="Transfer",
                                category_detailed="Payment",
                                payment_channel="ach"
                            )
                            transactions.append(debit_tx)
                            balances[checking_account.account_id] += -payment_amount
            
            current_date += timedelta(days=1)
        
        return transactions
    
    def _generate_savings_transfers(
        self, user_id: str, checking_account: Account, savings_account: Account,
        balances: Dict[str, float]
    ) -> List[Transaction]:
        """Generate savings transfers"""
        transactions = []
        
        # Generate 3-10 savings transfers
        num_transfers = random.randint(3, 10)
        
        for _ in range(num_transfers):
            tx_date = self._random_date(self.start_date, self.end_date)
            amount = random.uniform(50, 400)
            
            # Debit from checking
            debit_tx = self._create_transaction(
                checking_account.account_id,
                tx_date,
                -amount,
                merchant_name="Transfer to Savings",
                category_primary="Transfer",
                category_detailed="Savings",
                payment_channel="online"
            )
            transactions.append(debit_tx)
            balances[checking_account.account_id] += -amount
            
            # Credit to savings
            credit_tx = self._create_transaction(
                savings_account.account_id,
                tx_date,
                amount,
                merchant_name="Transfer from Checking",
                category_primary="Transfer",
                category_detailed="Savings",
                payment_channel="online"
            )
            transactions.append(credit_tx)
            balances[savings_account.account_id] += amount
        
        return transactions
    
    def _generate_hsa_transactions(
        self, user_id: str, hsa_account: Account, balances: Dict[str, float]
    ) -> List[Transaction]:
        """Generate HSA transactions (healthcare only)"""
        transactions = []
        
        # Generate 5-15 healthcare transactions
        num_transactions = random.randint(5, 15)
        
        for _ in range(num_transactions):
            tx_date = self._random_date(self.start_date, self.end_date)
            merchant_name, cat_primary, cat_detailed = random.choice(HEALTHCARE_MERCHANTS)
            amount = -random.uniform(20, 500)
            
            tx = self._create_transaction(
                hsa_account.account_id,
                tx_date,
                amount,
                merchant_name=merchant_name,
                category_primary=cat_primary,
                category_detailed=cat_detailed,
                payment_channel="card"
            )
            transactions.append(tx)
            balances[hsa_account.account_id] += amount
        
        return transactions
    
    def _generate_liabilities(self, accounts: List[Account], user_id: str) -> List[Liability]:
        """Generate liabilities for credit card accounts"""
        liabilities = []
        
        for account in accounts:
            if account.type == 'credit' and account.subtype == 'credit_card':
                # Calculate APR based on utilization
                utilization = (account.balance_current / account.balance_limit) if account.balance_limit else 0
                
                if utilization >= 0.8:
                    apr = random.uniform(22.0, 28.0)
                elif utilization >= 0.5:
                    apr = random.uniform(18.0, 24.0)
                else:
                    apr = random.uniform(12.0, 20.0)
                
                min_payment = max(account.balance_current * 0.02, 25.0)
                next_due = TODAY + timedelta(days=random.randint(1, 30))
                is_overdue = random.random() < 0.1  # 10% chance of overdue
                
                liabilities.append(Liability(
                    liability_id=f"{account.account_id}_liability",
                    account_id=account.account_id,
                    type='credit_card',
                    apr=round(apr, 2),
                    minimum_payment=round(min_payment, 2),
                    last_payment=round(min_payment, 2) if random.random() < 0.8 else None,
                    is_overdue=is_overdue,
                    next_payment_due=next_due,
                    last_statement_balance=round(account.balance_current, 2)
                ))
        
        return liabilities
    
    def _update_account_balances(self, accounts: List[Account], balances: Dict[str, float]):
        """Update account balances based on transaction history"""
        for account in accounts:
            if account.account_id in balances:
                account.balance_current = balances[account.account_id]
                account.balance_available = balances[account.account_id]
                
                # For credit cards, available = limit - current
                if account.type == 'credit' and account.balance_limit:
                    account.balance_available = account.balance_limit - balances[account.account_id]
    
    def _random_date(self, start: date, end: date) -> date:
        """Return random date between start and end"""
        delta = end - start
        return start + timedelta(days=random.randint(0, delta.days))
    
    def _create_transaction(
        self, account_id: str, date: date, amount: float,
        merchant_name: Optional[str] = None, category_primary: Optional[str] = None,
        category_detailed: Optional[str] = None, payment_channel: str = 'other',
        pending: bool = False, timestamp: Optional[datetime] = None
    ) -> Transaction:
        """Create a transaction object
        
        Args:
            timestamp: Optional datetime for the transaction. If None and this is a recurring
                      transaction (subscription, fixed expense), defaults to 7am US Central Time.
        """
        # If no timestamp provided and this is a recurring transaction, set to 7am Central Time
        if timestamp is None:
            # Check if this is a recurring transaction
            recurring_merchants = [
                'Rent Payment', 'Mortgage Payment', 'Electric Company', 'Internet Provider',
                'Phone Bill', 'Car Payment', 'Insurance', 'Netflix', 'Spotify',
                'Amazon Prime', 'Disney+', 'Hulu', 'Apple Music', 'Gym Membership',
                'Software Subscription', 'Newspaper'
            ]
            is_recurring = merchant_name in recurring_merchants
            
            if is_recurring:
                # Set to 7am US Central Time
                central_tz = pytz.timezone('US/Central')
                timestamp = central_tz.localize(datetime.combine(date, datetime.min.time().replace(hour=7)))
            else:
                # For non-recurring transactions, use midnight in Central Time
                central_tz = pytz.timezone('US/Central')
                timestamp = central_tz.localize(datetime.combine(date, datetime.min.time()))
        
        return Transaction(
            transaction_id=str(uuid.uuid4()),
            account_id=account_id,
            date=date,
            amount=round(amount, 2),
            merchant_name=merchant_name,
            merchant_entity_id=str(uuid.uuid4()) if merchant_name else None,
            payment_channel=payment_channel,
            category_primary=category_primary,
            category_detailed=category_detailed,
            pending=pending,
            timestamp=timestamp
        )

