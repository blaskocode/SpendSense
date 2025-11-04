"""Capital One synthetic-data library based generator for SpendSense"""

import random
import uuid
import numpy as np
import pandas as pd
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from synthetic_data.generators import TabularGenerator
from synthetic_data.generators import random_floats, random_integers, random_categorical, random_datetimes

from ..utils.config import NUM_USERS, SEED, DAYS_OF_HISTORY, TODAY
from ..utils.logger import setup_logger

# Import existing data structures
from .data_generator import User, Account, Transaction, Liability

logger = setup_logger(__name__)

# Set seed for reproducibility
random.seed(SEED)
np_rng = np.random.default_rng(SEED)  # NumPy random generator for Capital One library

# Helper functions to use Capital One generators with correct signatures
def _random_float(min_val: float, max_val: float) -> float:
    """Generate a random float using Capital One library"""
    return random_floats(np_rng, min=min_val, max=max_val, num_rows=1)[0]

def _random_floats(num: int, min_val: float, max_val: float) -> np.ndarray:
    """Generate multiple random floats using Capital One library"""
    return random_floats(np_rng, min=min_val, max=max_val, num_rows=num)

def _random_int(min_val: int, max_val: int) -> int:
    """Generate a random integer using Capital One library"""
    return int(random_integers(np_rng, min=min_val, max=max_val, num_rows=1)[0])

def _random_ints(num: int, min_val: int, max_val: int) -> np.ndarray:
    """Generate multiple random integers using Capital One library"""
    return random_integers(np_rng, min=min_val, max=max_val, num_rows=num)

def _random_category(categories: List[str]) -> str:
    """Generate a random category using Capital One library"""
    return random_categorical(np_rng, categories=categories, num_rows=1)[0]

def _random_categories(num: int, categories: List[str]) -> np.ndarray:
    """Generate multiple random categories using Capital One library"""
    return random_categorical(np_rng, categories=categories, num_rows=num)

# Income quartiles (annual)
INCOME_QUARTILES = [
    (20000, 40000),   # Q1: Low
    (40000, 65000),   # Q2: Lower-middle
    (65000, 100000),  # Q3: Upper-middle
    (100000, 200000), # Q4: High
]

# Account types and subtypes
ACCOUNT_TYPES = {
    'depository': ['checking', 'savings', 'money_market', 'hsa'],
    'credit': ['credit_card'],
}

# Common merchant categories
MERCHANT_CATEGORIES = {
    'Food and Drink': ['Restaurants', 'Fast Food', 'Groceries', 'Coffee Shops'],
    'Shops': ['Department Stores', 'Supermarkets', 'Gas Stations', 'Online Retail'],
    'Travel': ['Airlines', 'Hotels', 'Rideshare', 'Car Rental'],
    'Entertainment': ['Streaming Services', 'Movie Theaters', 'Concerts', 'Gaming'],
    'Bills': ['Utilities', 'Internet', 'Phone', 'Insurance'],
    'Healthcare': ['Pharmacies', 'Hospitals', 'Doctors', 'Dentists'],
    'Transportation': ['Gas Stations', 'Parking', 'Public Transit', 'Tolls'],
}

# Common subscription merchants
SUBSCRIPTION_MERCHANTS = [
    ('Netflix', 14.99, 'monthly'),
    ('Spotify', 9.99, 'monthly'),
    ('Amazon Prime', 14.99, 'monthly'),
    ('Disney+', 10.99, 'monthly'),
    ('Hulu', 12.99, 'monthly'),
    ('Apple Music', 9.99, 'monthly'),
    ('Gym Membership', 50.00, 'monthly'),
    ('Streaming Service', 15.99, 'monthly'),
    ('Software Subscription', 29.99, 'monthly'),
    ('Newspaper', 9.99, 'monthly'),
    ('Annual Subscription', 99.99, 'annually'),
    ('Insurance Premium', 150.00, 'monthly'),
]


class CapitalOneDataGenerator:
    """Generates synthetic banking data using Capital One's synthetic-data library"""
    
    def __init__(self, num_users: int = NUM_USERS, seed: int = SEED):
        self.num_users = num_users
        self.seed = seed
        random.seed(seed)
        global np_rng
        np_rng = np.random.default_rng(seed)  # Update global RNG
        self.start_date = TODAY - timedelta(days=DAYS_OF_HISTORY)
        self.end_date = TODAY - timedelta(days=1)
        
    def generate_all(self) -> Tuple[List[User], List[Account], List[Transaction], List[Liability]]:
        """Generate all synthetic data for all users"""
        logger.info(f"Generating synthetic data using Capital One library for {self.num_users} users")
        
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
        
        logger.info(f"Generated {len(users)} users, {len(accounts)} accounts, "
                   f"{len(transactions)} transactions, {len(liabilities)} liabilities")
        
        return users, accounts, transactions, liabilities
    
    def _generate_user_data(self, user_id: str) -> Tuple[List[Account], List[Transaction], List[Liability]]:
        """Generate accounts, transactions, and liabilities for a single user"""
        # Select income level using Capital One's random generator for better distribution
        income_quartile = random.choice(INCOME_QUARTILES)
        annual_income = _random_float(income_quartile[0], income_quartile[1])
        monthly_income = annual_income / 12
        
        # Select payroll frequency
        payroll_frequency = random.choice(['monthly', 'semi_monthly', 'biweekly'])
        
        # Generate accounts
        accounts = self._generate_accounts(user_id, monthly_income)
        
        # Generate transactions using Capital One's correlated generators
        transactions = []
        subscriptions = []
        
        for account in accounts:
            if account.type == 'depository':
                account_transactions, account_subscriptions = self._generate_depository_transactions(
                    account, user_id, monthly_income, payroll_frequency
                )
                transactions.extend(account_transactions)
                subscriptions.extend(account_subscriptions)
            elif account.type == 'credit':
                account_transactions = self._generate_credit_transactions(
                    account, user_id, monthly_income
                )
                transactions.extend(account_transactions)
        
        # Generate liabilities
        liabilities = self._generate_liabilities(accounts, user_id)
        
        return accounts, transactions, liabilities
    
    def _generate_accounts(self, user_id: str, monthly_income: float) -> List[Account]:
        """Generate accounts for a user using Capital One's random generators"""
        accounts = []
        
        # Always create a checking account
        checking_balance = _random_float(500, monthly_income * 2)
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
            savings_balance = _random_float(1000, monthly_income * 6)
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
            credit_limit = _random_float(monthly_income * 2, monthly_income * 10)
            balance = _random_float(0, credit_limit * 0.8)
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
            mm_balance = _random_float(5000, monthly_income * 12)
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
            hsa_balance = _random_float(1000, monthly_income * 3)
            accounts.append(Account(
                account_id=f"{user_id}_hsa",
                user_id=user_id,
                type='depository',
                subtype='hsa',
                balance_available=hsa_balance,
                balance_current=hsa_balance
            ))
        
        return accounts
    
    def _generate_depository_transactions(
        self, account: Account, user_id: str, monthly_income: float, payroll_frequency: str
    ) -> Tuple[List[Transaction], List[Dict]]:
        """Generate transactions for depository accounts using Capital One's generators"""
        transactions = []
        subscriptions = []
        
        current_date = self.start_date
        
        # Generate payroll dates
        payroll_dates = self._generate_payroll_dates(payroll_frequency, monthly_income)
        
        # Generate subscriptions using correlated data
        num_subscriptions = _random_int(2, 8)
        user_subscriptions = random.sample(SUBSCRIPTION_MERCHANTS, min(num_subscriptions, len(SUBSCRIPTION_MERCHANTS)))
        
        for merchant_name, base_amount, frequency in user_subscriptions:
            subscription = {
                'merchant_name': merchant_name,
                'amount': base_amount * _random_float(0.9, 1.1),  # Add variation
                'frequency': frequency,
                'start_date': current_date + timedelta(days=_random_int(0, 30)),
                'active': True,
                'account_id': account.account_id,
            }
            subscriptions.append(subscription)
        
        # Generate transaction amounts using correlated distributions
        # Use Capital One's random_floats for better statistical properties
        days_of_history = (self.end_date - self.start_date).days
        num_transactions = int(days_of_history * _random_float(0.3, 0.7))  # 30-70% of days have transactions
        
        # Generate transaction dates using random_datetimes
        import pandas as pd
        min_ts = pd.Timestamp(self.start_date)
        max_ts = pd.Timestamp(self.end_date)
        transaction_dates_raw = random_datetimes(
            np_rng,
            min=min_ts,
            max=max_ts,
            num_rows=num_transactions
        )
        # Convert to list of dates
        transaction_dates = []
        for d in transaction_dates_raw:
            if isinstance(d, (list, np.ndarray)):
                d = d[0] if len(d) > 0 else None
            if d is not None:
                if isinstance(d, str):
                    transaction_dates.append(datetime.strptime(d, "%B %d %Y %H:%M:%S").date())
                elif isinstance(d, datetime):
                    transaction_dates.append(d.date())
                elif isinstance(d, pd.Timestamp):
                    transaction_dates.append(d.date())
                else:
                    transaction_dates.append(pd.Timestamp(d).date())
        transaction_dates.sort()
        
        # Generate transaction amounts with correlation to income
        max_amount = min(monthly_income * 0.3, 5000)
        transaction_amounts = _random_floats(
            num_transactions,
            5,
            max_amount
        )
        
        # Generate categories using random_categorical
        categories = _random_categories(
            num_transactions,
            list(MERCHANT_CATEGORIES.keys())
        )
        
        # Generate transaction data
        transaction_idx = 0
        while current_date <= self.end_date:
            # Payroll deposits
            if current_date in payroll_dates:
                payroll_amount = monthly_income if payroll_frequency == 'monthly' else monthly_income / 2
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    payroll_amount,
                    merchant_name='Payroll Deposit',
                    category_primary='Transfer',
                    category_detailed='Payroll',
                    payment_channel='ach'
                ))
            
            # Subscription payments
            for sub in subscriptions:
                if not sub['active']:
                    continue
                
                days_since_start = (current_date - sub['start_date']).days
                
                if sub['frequency'] == 'monthly':
                    day_of_month = sub['start_date'].day
                    jitter = _random_int(-2, 2)
                    expected_day = max(1, min(28, day_of_month + jitter))
                    
                    if days_since_start > 0 and days_since_start % 30 < 3:
                        if abs(current_date.day - expected_day) <= 2:
                            if random.random() < 0.10:  # 10% cancellation
                                sub['active'] = False
                                continue
                            
                            if random.random() < 0.05:  # 5% price change
                                sub['amount'] = sub['amount'] * _random_float(0.95, 1.10)
                            
                            transactions.append(self._create_transaction(
                                account.account_id,
                                current_date,
                                -sub['amount'],
                                merchant_name=sub['merchant_name'],
                                category_primary='Entertainment',
                                category_detailed='Subscription',
                                payment_channel='other'
                            ))
                elif sub['frequency'] == 'annually':
                    if (current_date.month == sub['start_date'].month and 
                        abs(current_date.day - sub['start_date'].day) <= 2):
                        transactions.append(self._create_transaction(
                            account.account_id,
                            current_date,
                            -sub['amount'],
                            merchant_name=sub['merchant_name'],
                            category_primary='Entertainment',
                            category_detailed='Subscription',
                            payment_channel='other'
                        ))
            
            # Regular spending - use generated transaction dates and amounts
            if transaction_idx < len(transaction_dates) and transaction_dates[transaction_idx] == current_date:
                amount = -abs(transaction_amounts[transaction_idx])
                category = categories[transaction_idx]
                subcategory = random.choice(MERCHANT_CATEGORIES.get(category, ['Other']))
                
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    amount,
                    merchant_name=random.choice(['Merchant', 'Store', 'Restaurant', 'Online Store']),
                    category_primary=category,
                    category_detailed=subcategory,
                    payment_channel='other'
                ))
                transaction_idx += 1
            
            # Seasonal patterns
            if current_date.month == 12 and random.random() < 0.4:
                holiday_amount = _random_float(50, 500)
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    -holiday_amount,
                    merchant_name='Holiday Shopping',
                    category_primary='Shops',
                    category_detailed='Holiday',
                    payment_channel='other'
                ))
            
            if current_date.month == 4 and current_date.day == 15 and random.random() < 0.4:
                tax_refund = _random_float(500, 3000)
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    tax_refund,
                    merchant_name='Tax Refund',
                    category_primary='Transfer',
                    category_detailed='Tax Refund',
                    payment_channel='ach'
                ))
            
            # Life events
            days_of_history_total = (self.end_date - self.start_date).days
            if random.random() < 0.05 / days_of_history_total:
                event_type = random.choice(['major_purchase', 'medical', 'rent_increase'])
                if event_type == 'major_purchase' and random.random() < 0.03:
                    major_amount = _random_float(2000, 10000)
                    transactions.append(self._create_transaction(
                        account.account_id,
                        current_date,
                        -major_amount,
                        merchant_name='Major Purchase',
                        category_primary='Shops',
                        category_detailed='Major Purchase',
                        payment_channel='other'
                    ))
                elif event_type == 'medical' and random.random() < 0.10:
                    medical_amount = _random_float(200, 5000)
                    transactions.append(self._create_transaction(
                        account.account_id,
                        current_date,
                        -medical_amount,
                        merchant_name='Medical Expense',
                        category_primary='Healthcare',
                        category_detailed='Medical',
                        payment_channel='other'
                    ))
            
            # Edge cases
            if random.random() < 0.02:  # Overdraft
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    -_random_float(100, 500),
                    merchant_name='Overdraft Fee',
                    category_primary='Banking',
                    category_detailed='Overdraft',
                    payment_channel='other'
                ))
            
            if random.random() < 0.05:  # Refund
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    _random_float(20, 200),
                    merchant_name='Refund',
                    category_primary='Transfer',
                    category_detailed='Refund',
                    payment_channel='other'
                ))
            
            # Pending transactions (10% chance)
            if random.random() < 0.10:
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    -_random_float(10, 100),
                    merchant_name='Pending Transaction',
                    category_primary='Shops',
                    category_detailed='Pending',
                    payment_channel='other',
                    pending=True
                ))
            
            current_date += timedelta(days=1)
        
        return transactions, subscriptions
    
    def _generate_credit_transactions(self, account: Account, user_id: str, monthly_income: float) -> List[Transaction]:
        """Generate transactions for credit card accounts"""
        transactions = []
        current_date = self.start_date
        
        days_of_history = (self.end_date - self.start_date).days
        num_transactions = int(days_of_history * _random_float(0.15, 0.25))
        
        # Generate transaction dates
        import pandas as pd
        min_ts = pd.Timestamp(self.start_date)
        max_ts = pd.Timestamp(self.end_date)
        transaction_dates_raw = random_datetimes(
            np_rng,
            min=min_ts,
            max=max_ts,
            num_rows=num_transactions
        )
        # Convert to list of dates
        transaction_dates = []
        for d in transaction_dates_raw:
            if isinstance(d, (list, np.ndarray)):
                d = d[0] if len(d) > 0 else None
            if d is not None:
                if isinstance(d, str):
                    transaction_dates.append(datetime.strptime(d, "%B %d %Y %H:%M:%S").date())
                elif isinstance(d, datetime):
                    transaction_dates.append(d.date())
                elif isinstance(d, pd.Timestamp):
                    transaction_dates.append(d.date())
                else:
                    transaction_dates.append(pd.Timestamp(d).date())
        transaction_dates.sort()
        
        # Generate amounts
        max_amount = min(monthly_income * 0.2, 300)
        transaction_amounts = _random_floats(num_transactions, 10, max_amount)
        
        # Generate categories
        categories = _random_categories(num_transactions, list(MERCHANT_CATEGORIES.keys()))
        
        transaction_idx = 0
        while current_date <= self.end_date:
            # Credit card spending
            if transaction_idx < len(transaction_dates) and transaction_dates[transaction_idx] == current_date:
                amount = -abs(transaction_amounts[transaction_idx])
                category = categories[transaction_idx]
                subcategory = random.choice(MERCHANT_CATEGORIES.get(category, ['Other']))
                
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    amount,
                    merchant_name=random.choice(['Merchant', 'Store', 'Restaurant']),
                    category_primary=category,
                    category_detailed=subcategory,
                    payment_channel='other'
                ))
                transaction_idx += 1
            
            # Credit card payments (monthly)
            if current_date.day == 1 and random.random() < 0.8:
                payment_amount = min(account.balance_current * _random_float(0.1, 1.0), account.balance_limit)
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    payment_amount,
                    merchant_name='Credit Card Payment',
                    category_primary='Transfer',
                    category_detailed='Payment',
                    payment_channel='ach'
                ))
            
            current_date += timedelta(days=1)
        
        return transactions
    
    def _generate_liabilities(self, accounts: List[Account], user_id: str) -> List[Liability]:
        """Generate liabilities for accounts"""
        liabilities = []
        
        for account in accounts:
            if account.type == 'credit' and account.subtype == 'credit_card':
                apr = _random_float(12.0, 28.0)
                min_payment = max(account.balance_current * 0.02, 25.0)
                next_due = TODAY + timedelta(days=_random_int(1, 30))
                is_overdue = random.random() < 0.1
                
                liabilities.append(Liability(
                    liability_id=f"{account.account_id}_liability",
                    account_id=account.account_id,
                    type='credit_card',
                    apr=apr,
                    minimum_payment=min_payment,
                    last_payment=min_payment if random.random() < 0.8 else None,
                    is_overdue=is_overdue,
                    next_payment_due=next_due,
                    last_statement_balance=account.balance_current
                ))
        
        return liabilities
    
    def _generate_payroll_dates(self, frequency: str, monthly_income: float) -> List[date]:
        """Generate payroll deposit dates"""
        dates = []
        current_date = self.start_date
        
        if frequency == 'monthly':
            while current_date <= self.end_date:
                if current_date.day == 1:
                    dates.append(current_date)
                current_date += timedelta(days=1)
        elif frequency == 'semi_monthly':
            while current_date <= self.end_date:
                if current_date.day in [1, 15]:
                    dates.append(current_date)
                current_date += timedelta(days=1)
        elif frequency == 'biweekly':
            dates.append(current_date)
            while current_date <= self.end_date:
                current_date += timedelta(days=14)
                dates.append(current_date)
        
        return dates
    
    def _create_transaction(
        self, account_id: str, date: date, amount: float,
        merchant_name: Optional[str] = None, category_primary: Optional[str] = None,
        category_detailed: Optional[str] = None, payment_channel: str = 'other',
        pending: bool = False
    ) -> Transaction:
        """Create a transaction object"""
        return Transaction(
            transaction_id=str(uuid.uuid4()),
            account_id=account_id,
            date=date,
            amount=amount,
            merchant_name=merchant_name,
            merchant_entity_id=str(uuid.uuid4()) if merchant_name else None,
            payment_channel=payment_channel,
            category_primary=category_primary,
            category_detailed=category_detailed,
            pending=pending
        )

