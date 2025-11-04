"""Profile-based data generator using persona profiles for realistic transactions"""

import random
import uuid
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from ..utils.config import SEED, DAYS_OF_HISTORY, TODAY
from ..utils.logger import setup_logger
from .persona_profiles import (
    UserProfile, Persona, generate_all_persona_users
)
from .data_generator import User, Account, Transaction, Liability

logger = setup_logger(__name__)

# Set seed for reproducibility
random.seed(SEED)


class ProfileBasedGenerator:
    """Generates realistic banking data from persona profiles"""
    
    def __init__(self, num_users: int = 100, seed: int = SEED):
        self.num_users = num_users
        self.seed = seed
        random.seed(seed)
        self.start_date = TODAY - timedelta(days=DAYS_OF_HISTORY)
        self.end_date = TODAY - timedelta(days=1)
        
        # Generate profiles for all personas
        self.profiles = generate_all_persona_users(users_per_persona=num_users // 5)
        
        # Ensure we have exactly num_users
        if len(self.profiles) < num_users:
            # Add more variations if needed
            logger.warning(f"Only {len(self.profiles)} profiles generated, expected {num_users}")
        elif len(self.profiles) > num_users:
            # Trim to requested number
            self.profiles = self.profiles[:num_users]
    
    def generate_all(self) -> Tuple[List[User], List[Account], List[Transaction], List[Liability]]:
        """Generate all synthetic data from profiles"""
        logger.info(f"Generating data for {len(self.profiles)} users from profiles")
        
        users = []
        accounts = []
        transactions = []
        liabilities = []
        
        for i, profile in enumerate(self.profiles):
            user_id = f"user_{i+1:03d}"
            
            # Generate user
            user = User(
                user_id=user_id,
                created_at=self.start_date,
                last_updated=self.end_date
            )
            users.append(user)
            
            # Generate accounts and transactions from profile
            user_accounts, user_transactions, user_liabilities = self._generate_from_profile(
                user_id, profile
            )
            accounts.extend(user_accounts)
            transactions.extend(user_transactions)
            liabilities.extend(user_liabilities)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Generated data for {i+1}/{len(self.profiles)} users")
        
        logger.info(f"Generated {len(users)} users, {len(accounts)} accounts, "
                   f"{len(transactions)} transactions, {len(liabilities)} liabilities")
        
        return users, accounts, transactions, liabilities
    
    def _generate_from_profile(
        self, user_id: str, profile: UserProfile
    ) -> Tuple[List[Account], List[Transaction], List[Liability]]:
        """Generate accounts, transactions, and liabilities from a user profile"""
        
        # Generate accounts based on profile
        accounts = self._generate_accounts_from_profile(user_id, profile)
        
        # Map account subtypes to account objects
        account_map = {acc.subtype: acc for acc in accounts}
        
        # Generate transactions
        transactions = []
        
        # Generate payroll deposits
        payroll_transactions = self._generate_payroll_deposits(
            user_id, profile, account_map.get('checking')
        )
        transactions.extend(payroll_transactions)
        
        # Generate recurring payments
        recurring_transactions = self._generate_recurring_payments(
            user_id, profile, account_map
        )
        transactions.extend(recurring_transactions)
        
        # Generate spending patterns
        spending_transactions = self._generate_spending_patterns(
            user_id, profile, account_map
        )
        transactions.extend(spending_transactions)
        
        # Generate savings contributions (if applicable)
        if profile.savings_contribution_monthly:
            savings_transactions = self._generate_savings_contributions(
                user_id, profile, account_map
            )
            transactions.extend(savings_transactions)
        
        # Generate credit card payments (if applicable)
        if 'credit_card' in profile.accounts and profile.credit_limit:
            credit_payments = self._generate_credit_card_payments(
                user_id, profile, account_map
            )
            transactions.extend(credit_payments)
        
        # Generate liabilities
        liabilities = self._generate_liabilities_from_profile(accounts, user_id, profile)
        
        return accounts, transactions, liabilities
    
    def _generate_accounts_from_profile(
        self, user_id: str, profile: UserProfile
    ) -> List[Account]:
        """Generate accounts based on profile specifications"""
        accounts = []
        monthly_income = profile.income_annual / 12
        
        # Always create checking account
        checking_balance = random.uniform(500, monthly_income * 2)
        accounts.append(Account(
            account_id=f"{user_id}_checking",
            user_id=user_id,
            type='depository',
            subtype='checking',
            balance_available=checking_balance,
            balance_current=checking_balance
        ))
        
        # Create accounts based on profile
        if 'savings' in profile.accounts:
            savings_balance = random.uniform(1000, monthly_income * 6)
            accounts.append(Account(
                account_id=f"{user_id}_savings",
                user_id=user_id,
                type='depository',
                subtype='savings',
                balance_available=savings_balance,
                balance_current=savings_balance
            ))
        
        if 'credit_card' in profile.accounts and profile.credit_limit:
            credit_limit = profile.credit_limit
            credit_balance = profile.credit_balance_start or 0
            accounts.append(Account(
                account_id=f"{user_id}_credit",
                user_id=user_id,
                type='credit',
                subtype='credit_card',
                balance_available=credit_limit - credit_balance,
                balance_current=credit_balance,
                balance_limit=credit_limit
            ))
        
        if 'hsa' in profile.accounts:
            hsa_balance = random.uniform(1000, monthly_income * 3)
            accounts.append(Account(
                account_id=f"{user_id}_hsa",
                user_id=user_id,
                type='depository',
                subtype='hsa',
                balance_available=hsa_balance,
                balance_current=hsa_balance
            ))
        
        if 'money_market' in profile.accounts:
            mm_balance = random.uniform(5000, monthly_income * 12)
            accounts.append(Account(
                account_id=f"{user_id}_money_market",
                user_id=user_id,
                type='depository',
                subtype='money_market',
                balance_available=mm_balance,
                balance_current=mm_balance
            ))
        
        return accounts
    
    def _generate_payroll_deposits(
        self, user_id: str, profile: UserProfile, checking_account: Optional[Account]
    ) -> List[Transaction]:
        """Generate payroll deposits based on profile frequency"""
        if not checking_account:
            return []
        
        transactions = []
        monthly_income = profile.income_annual / 12
        current_date = self.start_date
        
        payroll_amounts = {
            'monthly': monthly_income,
            'semi_monthly': monthly_income / 2,
            'biweekly': monthly_income * 26 / 12 / 2  # Approximate biweekly
        }
        
        amount = payroll_amounts.get(profile.payroll_frequency, monthly_income)
        
        if profile.payroll_frequency == 'monthly':
            # First of each month
            while current_date <= self.end_date:
                if current_date.day == 1:
                    transactions.append(self._create_transaction(
                        checking_account.account_id,
                        current_date,
                        amount,
                        merchant_name='Payroll Deposit',
                        category_primary='Transfer',
                        category_detailed='Payroll',
                        payment_channel='ach'
                    ))
                current_date += timedelta(days=1)
        
        elif profile.payroll_frequency == 'semi_monthly':
            # 1st and 15th of each month
            while current_date <= self.end_date:
                if current_date.day in [1, 15]:
                    transactions.append(self._create_transaction(
                        checking_account.account_id,
                        current_date,
                        amount,
                        merchant_name='Payroll Deposit',
                        category_primary='Transfer',
                        category_detailed='Payroll',
                        payment_channel='ach'
                    ))
                current_date += timedelta(days=1)
        
        elif profile.payroll_frequency == 'biweekly':
            # Every 14 days, but for variable income, add irregularity
            if profile.persona == Persona.VARIABLE_INCOME:
                # Irregular paychecks - gaps of 30-60 days
                current_date = self.start_date
                while current_date <= self.end_date:
                    transactions.append(self._create_transaction(
                        checking_account.account_id,
                        current_date,
                        amount * random.uniform(0.7, 1.3),  # Variable amounts
                        merchant_name='Payroll Deposit',
                        category_primary='Transfer',
                        category_detailed='Payroll',
                        payment_channel='ach'
                    ))
                    # Next paycheck in 30-60 days (irregular)
                    current_date += timedelta(days=random.randint(30, 60))
            else:
                # Regular biweekly
                current_date = self.start_date
                while current_date <= self.end_date:
                    transactions.append(self._create_transaction(
                        checking_account.account_id,
                        current_date,
                        amount,
                        merchant_name='Payroll Deposit',
                        category_primary='Transfer',
                        category_detailed='Payroll',
                        payment_channel='ach'
                    ))
                    current_date += timedelta(days=14)
        
        return transactions
    
    def _generate_recurring_payments(
        self, user_id: str, profile: UserProfile, account_map: Dict[str, Account]
    ) -> List[Transaction]:
        """Generate recurring payments on their specified days"""
        transactions = []
        
        # Track which months we've processed each payment
        payment_months = set()
        
        # Process each month separately to avoid duplicates
        current_month = self.start_date.replace(day=1)
        end_month = self.end_date.replace(day=1)
        
        while current_month <= end_month:
            # Process all payments for this month
            for payment in profile.recurring_payments:
                # Skip if account doesn't exist
                account = account_map.get(payment.account_subtype)
                if not account:
                    continue
                
                # Check if we've already processed this payment this month
                month_key = (current_month.year, current_month.month, payment.merchant_name)
                if month_key in payment_months:
                    continue
                
                # Calculate target day for this month (with jitter)
                base_day = payment.day_of_month
                jitter = random.randint(-payment.jitter_days, payment.jitter_days)
                target_day = max(1, min(28, base_day + jitter))
                
                # Create payment date for this month
                try:
                    payment_date = date(current_month.year, current_month.month, target_day)
                except ValueError:
                    # Handle invalid dates (e.g., Feb 30)
                    payment_date = date(current_month.year, current_month.month, 28)
                
                # Only create if date is within our range
                if self.start_date <= payment_date <= self.end_date:
                    # Handle special cases
                    if 'savings' in payment.merchant_name.lower() or 'transfer' in payment.merchant_name.lower():
                        # Savings transfer - positive amount
                        amount = abs(payment.amount)
                    else:
                        # Regular payment - negative amount
                        amount = payment.amount
                    
                    transactions.append(self._create_transaction(
                        account.account_id,
                        payment_date,
                        amount,
                        merchant_name=payment.merchant_name,
                        category_primary=payment.category_primary,
                        category_detailed=payment.category_detailed,
                        payment_channel='ach' if 'transfer' in payment.category_detailed.lower() or 'payment' in payment.category_detailed.lower() else 'other'
                    ))
                    
                    payment_months.add(month_key)
            
            # Move to next month
            if current_month.month == 12:
                current_month = date(current_month.year + 1, 1, 1)
            else:
                current_month = date(current_month.year, current_month.month + 1, 1)
        
        return transactions
    
    def _generate_spending_patterns(
        self, user_id: str, profile: UserProfile, account_map: Dict[str, Account]
    ) -> List[Transaction]:
        """Generate variable spending based on patterns"""
        transactions = []
        
        # Calculate how many transactions per pattern
        days_of_history = (self.end_date - self.start_date).days
        months = days_of_history / 30.0
        
        for pattern in profile.spending_patterns:
            account = account_map.get(pattern.account_subtype)
            if not account:
                continue
            
            # Total transactions for this pattern
            total_transactions = int(pattern.frequency_per_month * months)
            
            # Distribute transactions across the date range
            for i in range(total_transactions):
                # Random date within range
                days_offset = random.randint(0, days_of_history - 1)
                transaction_date = self.start_date + timedelta(days=days_offset)
                
                # Random amount within range
                amount = random.uniform(pattern.amount_range[0], pattern.amount_range[1])
                
                # Generate merchant name based on category
                merchant_name = self._generate_merchant_name(pattern.category_detailed)
                
                transactions.append(self._create_transaction(
                    account.account_id,
                    transaction_date,
                    amount,
                    merchant_name=merchant_name,
                    category_primary=pattern.category_primary,
                    category_detailed=pattern.category_detailed,
                    payment_channel='other'
                ))
        
        return transactions
    
    def _generate_savings_contributions(
        self, user_id: str, profile: UserProfile, account_map: Dict[str, Account]
    ) -> List[Transaction]:
        """Generate savings contributions"""
        transactions = []
        
        checking = account_map.get('checking')
        savings = account_map.get('savings')
        
        if not checking or not savings or not profile.savings_contribution_monthly:
            return []
        
        current_date = self.start_date
        
        while current_date <= self.end_date:
            if current_date.day == profile.savings_contribution_day:
                amount = profile.savings_contribution_monthly * random.uniform(0.95, 1.05)
                
                # Debit from checking
                transactions.append(self._create_transaction(
                    checking.account_id,
                    current_date,
                    -amount,
                    merchant_name='Savings Transfer',
                    category_primary='Transfer',
                    category_detailed='Savings',
                    payment_channel='ach'
                ))
                
                # Credit to savings
                transactions.append(self._create_transaction(
                    savings.account_id,
                    current_date,
                    amount,
                    merchant_name='Savings Transfer',
                    category_primary='Transfer',
                    category_detailed='Savings',
                    payment_channel='ach'
                ))
            
            current_date += timedelta(days=1)
        
        return transactions
    
    def _generate_credit_card_payments(
        self, user_id: str, profile: UserProfile, account_map: Dict[str, Account]
    ) -> List[Transaction]:
        """Generate credit card payments"""
        transactions = []
        
        checking = account_map.get('checking')
        credit_card = account_map.get('credit_card')
        
        if not checking or not credit_card:
            return []
        
        # Track credit card balance
        credit_balance = profile.credit_balance_start or 0
        credit_limit = profile.credit_limit or 0
        
        current_date = self.start_date
        
        # Generate payments monthly (around day 25, with jitter)
        while current_date <= self.end_date:
            if current_date.day in range(23, 28):  # Payment window
                if random.random() < 0.8:  # 80% chance of payment
                    if profile.min_payment_only:
                        # Minimum payment (typically 2% of balance or $25, whichever is higher)
                        payment_amount = max(credit_balance * 0.02, 25.0)
                    else:
                        # Pay in full or substantial amount
                        payment_amount = min(credit_balance * random.uniform(0.8, 1.0), credit_limit)
                    
                    payment_amount = round(payment_amount, 2)
                    
                    if payment_amount > 0:
                        transactions.append(self._create_transaction(
                            credit_card.account_id,
                            current_date,
                            payment_amount,
                            merchant_name='Credit Card Payment',
                            category_primary='Transfer',
                            category_detailed='Payment',
                            payment_channel='ach'
                        ))
                        
                        # Update balance (simplified - actual balance tracking would be more complex)
                        credit_balance = max(0, credit_balance - payment_amount)
            
            current_date += timedelta(days=1)
        
        return transactions
    
    def _generate_liabilities_from_profile(
        self, accounts: List[Account], user_id: str, profile: UserProfile
    ) -> List[Liability]:
        """Generate liabilities based on profile"""
        liabilities = []
        
        for account in accounts:
            if account.type == 'credit' and account.subtype == 'credit_card':
                # Calculate APR based on utilization
                utilization = (account.balance_current / account.balance_limit) if account.balance_limit else 0
                
                # Higher utilization = higher APR
                if utilization >= 0.8:
                    apr = random.uniform(22.0, 28.0)
                elif utilization >= 0.5:
                    apr = random.uniform(18.0, 24.0)
                else:
                    apr = random.uniform(12.0, 20.0)
                
                # Minimum payment
                min_payment = max(account.balance_current * 0.02, 25.0)
                
                # Overdue status (for high utilization users)
                is_overdue = False
                if profile.persona == Persona.HIGH_UTILIZATION:
                    is_overdue = random.random() < 0.3  # 30% chance of overdue
                
                next_due = TODAY + timedelta(days=random.randint(1, 30))
                
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
    
    def _generate_merchant_name(self, category: str) -> str:
        """Generate realistic merchant name based on category"""
        merchants = {
            'Groceries': ['Whole Foods', 'Safeway', 'Kroger', 'Walmart', 'Target', 'Grocery Store'],
            'Fast Food': ['McDonald\'s', 'Burger King', 'Taco Bell', 'Subway', 'Pizza Hut'],
            'Restaurants': ['Restaurant', 'Dining', 'Local Eatery', 'Cafe', 'Bistro'],
            'Gas Stations': ['Shell', 'Exxon', 'BP', 'Chevron', 'Gas Station'],
            'Online Retail': ['Amazon', 'eBay', 'Online Store', 'E-commerce'],
        }
        
        return random.choice(merchants.get(category, ['Merchant', 'Store']))
    
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

