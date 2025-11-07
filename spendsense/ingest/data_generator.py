"""Synthetic data generator for SpendSense"""

import random
import uuid
from datetime import date, timedelta, datetime
import pytz
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from ..utils.config import NUM_USERS, SEED, DAYS_OF_HISTORY, TODAY
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# Set seed for reproducibility
random.seed(SEED)

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


@dataclass
class User:
    """User data structure"""
    user_id: str
    created_at: date
    consent_status: bool = False
    consent_timestamp: Optional[datetime] = None
    last_updated: date = None


@dataclass
class Account:
    """Account data structure"""
    account_id: str
    user_id: str
    type: str
    subtype: str
    balance_available: float
    balance_current: float
    balance_limit: Optional[float] = None
    iso_currency_code: str = 'USD'


@dataclass
class Transaction:
    """Transaction data structure"""
    transaction_id: str
    account_id: str
    date: date
    amount: float
    merchant_name: Optional[str] = None
    merchant_entity_id: Optional[str] = None
    payment_channel: str = 'other'
    category_primary: Optional[str] = None
    category_detailed: Optional[str] = None
    pending: bool = False
    timestamp: Optional[datetime] = None  # Timestamp for the transaction (timezone-aware)


@dataclass
class Liability:
    """Liability data structure"""
    liability_id: str
    account_id: str
    type: str
    apr: Optional[float] = None
    minimum_payment: Optional[float] = None
    last_payment: Optional[float] = None
    is_overdue: bool = False
    next_payment_due: Optional[date] = None
    last_statement_balance: Optional[float] = None


class SyntheticDataGenerator:
    """Generates synthetic banking data with realistic variability"""
    
    def __init__(self, num_users: int = NUM_USERS, seed: int = SEED):
        self.num_users = num_users
        self.seed = seed
        random.seed(seed)
        self.start_date = TODAY - timedelta(days=DAYS_OF_HISTORY)
        self.end_date = TODAY - timedelta(days=1)
        
    def generate_all(self) -> Tuple[List[User], List[Account], List[Transaction], List[Liability]]:
        """Generate all synthetic data"""
        logger.info(f"Generating synthetic data for {self.num_users} users")
        
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
        # Select income level
        income_quartile = random.choice(INCOME_QUARTILES)
        annual_income = random.uniform(income_quartile[0], income_quartile[1])
        monthly_income = annual_income / 12
        
        # Select payroll frequency
        payroll_frequency = random.choice(['monthly', 'semi_monthly', 'biweekly'])
        
        # Generate accounts
        accounts = self._generate_accounts(user_id, monthly_income)
        
        # Generate transactions
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
    
    def _generate_depository_transactions(
        self, account: Account, user_id: str, monthly_income: float, payroll_frequency: str
    ) -> Tuple[List[Transaction], List[Dict]]:
        """Generate transactions for depository accounts"""
        transactions = []
        subscriptions = []
        
        current_date = self.start_date
        
        # Generate payroll deposits
        payroll_dates = self._generate_payroll_dates(payroll_frequency, monthly_income)
        
        # Generate subscriptions
        num_subscriptions = random.randint(2, 8)
        user_subscriptions = random.sample(SUBSCRIPTION_MERCHANTS, min(num_subscriptions, len(SUBSCRIPTION_MERCHANTS)))
        
        for merchant_name, base_amount, frequency in user_subscriptions:
            subscription = {
                'merchant_name': merchant_name,
                'amount': base_amount,
                'frequency': frequency,
                'start_date': current_date,
                'active': True,
                'account_id': account.account_id,
            }
            subscriptions.append(subscription)
        
        # Generate transactions day by day
        while current_date <= self.end_date:
            # Payroll deposits
            if current_date in payroll_dates:
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    monthly_income if payroll_frequency == 'monthly' else monthly_income / 2,
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
                    # Check if it's approximately the subscription day each month (with jitter)
                    day_of_month = sub['start_date'].day
                    jitter = random.randint(-2, 2)
                    expected_day = max(1, min(28, day_of_month + jitter))  # Keep within valid range
                    
                    # Check if this is a monthly payment date (approximately every 30 days)
                    if days_since_start > 0 and days_since_start % 30 < 3:  # Allow 3-day window
                        if abs(current_date.day - expected_day) <= 2:  # Within 2 days of expected
                            # 10% chance of cancellation
                            if random.random() < 0.10:
                                sub['active'] = False
                                continue
                            
                            # 5% chance of price change
                            amount = sub['amount']
                            if random.random() < 0.05:
                                amount = sub['amount'] * random.uniform(0.95, 1.10)
                            
                            transactions.append(self._create_transaction(
                                account.account_id,
                                current_date,
                                -amount,
                                merchant_name=sub['merchant_name'],
                                category_primary='Entertainment',
                                category_detailed='Subscription',
                                payment_channel='other'
                            ))
                elif sub['frequency'] == 'annually':
                    # Annual subscriptions - check if same month and day (with jitter)
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
            
            # Regular spending (daily)
            if random.random() < 0.3:  # 30% chance of transaction per day
                amount = -random.uniform(5, 150)
                category = random.choice(list(MERCHANT_CATEGORIES.keys()))
                subcategory = random.choice(MERCHANT_CATEGORIES[category])
                
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    amount,
                    merchant_name=random.choice(['Merchant', 'Store', 'Restaurant']),
                    category_primary=category,
                    category_detailed=subcategory,
                    payment_channel='other'
                ))
            
            # Seasonal patterns
            if current_date.month == 12:  # December - holiday spending
                if random.random() < 0.4:  # 40% chance of holiday transaction
                    transactions.append(self._create_transaction(
                        account.account_id,
                        current_date,
                        -random.uniform(50, 500),
                        merchant_name='Holiday Shopping',
                        category_primary='Shops',
                        category_detailed='Holiday',
                        payment_channel='other'
                    ))
            
            if current_date.month == 4:  # April - tax refunds
                if random.random() < 0.4 and current_date.day == 15:  # Tax day
                    transactions.append(self._create_transaction(
                        account.account_id,
                        current_date,
                        random.uniform(500, 3000),
                        merchant_name='Tax Refund',
                        category_primary='Transfer',
                        category_detailed='Tax Refund',
                        payment_channel='ach'
                    ))
            
            # Life events (5% chance per user over entire period, 3% major purchase, 10% medical)
            days_of_history = (self.end_date - self.start_date).days
            if random.random() < 0.05 / days_of_history:  # 5% chance over entire period
                event_type = random.choice(['major_purchase', 'medical', 'rent_increase'])
                if event_type == 'major_purchase' and random.random() < 0.03:
                    transactions.append(self._create_transaction(
                        account.account_id,
                        current_date,
                        -random.uniform(2000, 10000),
                        merchant_name='Major Purchase',
                        category_primary='Shops',
                        category_detailed='Major Purchase',
                        payment_channel='other'
                    ))
                elif event_type == 'medical' and random.random() < 0.10:
                    transactions.append(self._create_transaction(
                        account.account_id,
                        current_date,
                        -random.uniform(200, 5000),
                        merchant_name='Medical Expense',
                        category_primary='Healthcare',
                        category_detailed='Medical',
                        payment_channel='other'
                    ))
            
            # Edge cases
            if random.random() < 0.02:  # 2% chance of overdraft
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    -random.uniform(100, 500),
                    merchant_name='Overdraft Fee',
                    category_primary='Banking',
                    category_detailed='Overdraft',
                    payment_channel='other'
                ))
            
            if random.random() < 0.05:  # 5% chance of refund
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    random.uniform(20, 200),
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
                    -random.uniform(10, 100),
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
        
        while current_date <= self.end_date:
            # Credit card spending (less frequent than checking)
            if random.random() < 0.2:  # 20% chance per day
                amount = -random.uniform(10, 300)
                category = random.choice(list(MERCHANT_CATEGORIES.keys()))
                subcategory = random.choice(MERCHANT_CATEGORIES[category])
                
                transactions.append(self._create_transaction(
                    account.account_id,
                    current_date,
                    amount,
                    merchant_name=random.choice(['Merchant', 'Store', 'Restaurant']),
                    category_primary=category,
                    category_detailed=subcategory,
                    payment_channel='other'
                ))
            
            # Credit card payments (monthly)
            if current_date.day == 1 and random.random() < 0.8:  # 80% chance of payment on 1st
                payment_amount = min(account.balance_current * random.uniform(0.1, 1.0), account.balance_limit)
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
                # Credit card liability
                apr = random.uniform(12.0, 28.0)
                min_payment = max(account.balance_current * 0.02, 25.0)
                next_due = TODAY + timedelta(days=random.randint(1, 30))
                is_overdue = random.random() < 0.1  # 10% chance of overdue
                
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
            # First of each month
            while current_date <= self.end_date:
                if current_date.day == 1:
                    dates.append(current_date)
                current_date += timedelta(days=1)
        elif frequency == 'semi_monthly':
            # 1st and 15th of each month
            while current_date <= self.end_date:
                if current_date.day in [1, 15]:
                    dates.append(current_date)
                current_date += timedelta(days=1)
        elif frequency == 'biweekly':
            # Every 14 days starting from start_date
            dates.append(current_date)
            while current_date <= self.end_date:
                current_date += timedelta(days=14)
                dates.append(current_date)
        
        return dates
    
    def _create_transaction(
        self, account_id: str, date: date, amount: float,
        merchant_name: Optional[str] = None, category_primary: Optional[str] = None,
        category_detailed: Optional[str] = None, payment_channel: str = 'other',
        pending: bool = False, timestamp: Optional[datetime] = None
    ) -> Transaction:
        """Create a transaction object
        
        Args:
            timestamp: Optional datetime for the transaction. If None, defaults to midnight Central Time.
        """
        # If no timestamp provided, use midnight in Central Time
        if timestamp is None:
            central_tz = pytz.timezone('US/Central')
            timestamp = central_tz.localize(datetime.combine(date, datetime.min.time()))
        
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
            pending=pending,
            timestamp=timestamp
        )

