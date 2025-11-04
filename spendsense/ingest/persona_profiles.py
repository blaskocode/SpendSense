"""Persona-based user profiles for realistic data generation"""

import random
import copy
from dataclasses import dataclass, replace
from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta
from enum import Enum


class Persona(Enum):
    """Persona types"""
    HIGH_UTILIZATION = "High Utilization"
    VARIABLE_INCOME = "Variable Income Budgeter"
    CREDIT_BUILDER = "Credit Builder"
    SUBSCRIPTION_HEAVY = "Subscription-Heavy"
    SAVINGS_BUILDER = "Savings Builder"


@dataclass
class RecurringPayment:
    """A recurring payment pattern"""
    merchant_name: str
    amount: float
    day_of_month: int  # Fixed day (1-31) or -1 for flexible
    account_subtype: str  # 'checking', 'credit_card', 'hsa', etc.
    category_primary: str
    category_detailed: str
    frequency: str  # 'monthly', 'biweekly', 'weekly'
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    jitter_days: int = 0  # Allow ±N days variation


@dataclass
class SpendingPattern:
    """A spending pattern (groceries, gas, etc.)"""
    category_primary: str
    category_detailed: str
    frequency_per_month: int  # How many times per month
    amount_range: Tuple[float, float]  # (min, max)
    account_subtype: str  # Which account type to use
    days_of_week: Optional[List[int]] = None  # 0=Monday, 6=Sunday, None=any day


@dataclass
class UserProfile:
    """A complete user profile with realistic transaction patterns"""
    profile_id: str
    persona: Persona
    income_annual: float
    income_quartile: int  # 1-4
    payroll_frequency: str  # 'monthly', 'semi_monthly', 'biweekly'
    accounts: List[str]  # ['checking', 'savings', 'credit_card', 'hsa', 'money_market']
    
    # Regular bills (rent, utilities, etc.)
    recurring_payments: List[RecurringPayment]
    
    # Spending patterns (groceries, gas, restaurants)
    spending_patterns: List[SpendingPattern]
    
    # Credit card details (if applicable)
    credit_limit: Optional[float] = None
    credit_balance_start: Optional[float] = None  # Starting balance
    credit_utilization_target: Optional[float] = None  # Target utilization %
    min_payment_only: bool = False  # Only makes minimum payments
    
    # Savings behavior
    savings_contribution_monthly: Optional[float] = None
    savings_contribution_day: Optional[int] = None  # Day of month
    
    # Notes for profile
    description: str = ""


# ============================================================================
# HIGH UTILIZATION PERSONA PROFILES
# ============================================================================

def create_high_utilization_profile_1() -> UserProfile:
    """High Utilization User 1: Maxed out credit card, high interest"""
    return UserProfile(
        profile_id="high_util_1",
        persona=Persona.HIGH_UTILIZATION,
        income_annual=45000,
        income_quartile=1,
        payroll_frequency='biweekly',
        accounts=['checking', 'credit_card'],
        recurring_payments=[
            RecurringPayment(
                merchant_name='Rent Payment',
                amount=-1200.0,
                day_of_month=1,
                account_subtype='checking',
                category_primary='Bills',
                category_detailed='Rent',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Electric Company',
                amount=-120.0,
                day_of_month=5,
                account_subtype='checking',
                category_primary='Bills',
                category_detailed='Utilities',
                frequency='monthly',
                jitter_days=2
            ),
            RecurringPayment(
                merchant_name='Internet Provider',
                amount=-79.99,
                day_of_month=10,
                account_subtype='checking',
                category_primary='Bills',
                category_detailed='Internet',
                frequency='monthly',
                jitter_days=1
            ),
            RecurringPayment(
                merchant_name='Netflix',
                amount=-14.99,
                day_of_month=15,
                account_subtype='credit_card',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Spotify',
                amount=-9.99,
                day_of_month=20,
                account_subtype='credit_card',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Credit Card Payment',
                amount=-150.0,  # Minimum payment only
                day_of_month=25,
                account_subtype='checking',
                category_primary='Transfer',
                category_detailed='Payment',
                frequency='monthly',
                jitter_days=2
            ),
        ],
        spending_patterns=[
            SpendingPattern(
                category_primary='Food and Drink',
                category_detailed='Groceries',
                frequency_per_month=4,
                amount_range=(-120.0, -80.0),
                account_subtype='credit_card'
            ),
            SpendingPattern(
                category_primary='Food and Drink',
                category_detailed='Fast Food',
                frequency_per_month=8,
                amount_range=(-25.0, -12.0),
                account_subtype='credit_card'
            ),
            SpendingPattern(
                category_primary='Transportation',
                category_detailed='Gas Stations',
                frequency_per_month=6,
                amount_range=(-60.0, -40.0),
                account_subtype='credit_card'
            ),
        ],
        credit_limit=5000.0,
        credit_balance_start=4500.0,  # 90% utilization
        credit_utilization_target=0.90,
        min_payment_only=True,
        description="High credit utilization (90%), minimum payments only, high interest charges"
    )


def create_high_utilization_profile_2() -> UserProfile:
    """High Utilization User 2: Overdue account, multiple cards"""
    return UserProfile(
        profile_id="high_util_2",
        persona=Persona.HIGH_UTILIZATION,
        income_annual=52000,
        income_quartile=2,
        payroll_frequency='semi_monthly',
        accounts=['checking', 'savings', 'credit_card'],
        recurring_payments=[
            RecurringPayment(
                merchant_name='Rent Payment',
                amount=-1400.0,
                day_of_month=1,
                account_subtype='checking',
                category_primary='Bills',
                category_detailed='Rent',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Car Payment',
                amount=-350.0,
                day_of_month=3,
                account_subtype='checking',
                category_primary='Bills',
                category_detailed='Auto Loan',
                frequency='monthly',
                jitter_days=1
            ),
            RecurringPayment(
                merchant_name='Credit Card Payment',
                amount=-200.0,  # Minimum payment
                day_of_month=15,
                account_subtype='checking',
                category_primary='Transfer',
                category_detailed='Payment',
                frequency='monthly',
                jitter_days=3  # Often late
            ),
            RecurringPayment(
                merchant_name='Amazon Prime',
                amount=-14.99,
                day_of_month=5,
                account_subtype='credit_card',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
        ],
        spending_patterns=[
            SpendingPattern(
                category_primary='Food and Drink',
                category_detailed='Groceries',
                frequency_per_month=3,
                amount_range=(-150.0, -100.0),
                account_subtype='credit_card'
            ),
            SpendingPattern(
                category_primary='Shops',
                category_detailed='Online Retail',
                frequency_per_month=6,
                amount_range=(-80.0, -30.0),
                account_subtype='credit_card'
            ),
        ],
        credit_limit=8000.0,
        credit_balance_start=6000.0,  # 75% utilization
        credit_utilization_target=0.75,
        min_payment_only=True,
        description="Overdue payments, 75% utilization, frequently late"
    )


# ============================================================================
# VARIABLE INCOME BUDGETER PERSONA PROFILES
# ============================================================================

def create_variable_income_profile_1() -> UserProfile:
    """Variable Income User 1: Freelancer with irregular income"""
    return UserProfile(
        profile_id="var_income_1",
        persona=Persona.VARIABLE_INCOME,
        income_annual=38000,  # Variable, this is average
        income_quartile=1,
        payroll_frequency='monthly',  # But irregular dates
        accounts=['checking', 'savings'],
        recurring_payments=[
            RecurringPayment(
                merchant_name='Rent Payment',
                amount=-950.0,
                day_of_month=1,
                account_subtype='checking',
                category_primary='Bills',
                category_detailed='Rent',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Phone Bill',
                amount=-85.0,
                day_of_month=8,
                account_subtype='checking',
                category_primary='Bills',
                category_detailed='Phone',
                frequency='monthly',
                jitter_days=2
            ),
            RecurringPayment(
                merchant_name='Netflix',
                amount=-14.99,
                day_of_month=12,
                account_subtype='checking',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
        ],
        spending_patterns=[
            SpendingPattern(
                category_primary='Food and Drink',
                category_detailed='Groceries',
                frequency_per_month=3,
                amount_range=(-100.0, -60.0),
                account_subtype='checking'
            ),
            SpendingPattern(
                category_primary='Food and Drink',
                category_detailed='Restaurants',
                frequency_per_month=2,
                amount_range=(-40.0, -20.0),
                account_subtype='checking'
            ),
        ],
        description="Freelancer with irregular income, gaps between paychecks >45 days"
    )


# ============================================================================
# CREDIT BUILDER PERSONA PROFILES
# ============================================================================

def create_credit_builder_profile_1() -> UserProfile:
    """Credit Builder User 1: No credit cards, building credit"""
    return UserProfile(
        profile_id="credit_builder_1",
        persona=Persona.CREDIT_BUILDER,
        income_annual=35000,
        income_quartile=1,
        payroll_frequency='biweekly',
        accounts=['checking', 'savings'],
        recurring_payments=[
            RecurringPayment(
                merchant_name='Rent Payment',
                amount=-800.0,
                day_of_month=1,
                account_subtype='checking',
                category_primary='Bills',
                category_detailed='Rent',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Netflix',
                amount=-14.99,
                day_of_month=10,
                account_subtype='checking',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
        ],
        spending_patterns=[
            SpendingPattern(
                category_primary='Food and Drink',
                category_detailed='Groceries',
                frequency_per_month=4,
                amount_range=(-80.0, -50.0),
                account_subtype='checking'
            ),
        ],
        description="No credit cards, just checking and savings, building credit history"
    )


# ============================================================================
# SUBSCRIPTION-HEAVY PERSONA PROFILES
# ============================================================================

def create_subscription_heavy_profile_1() -> UserProfile:
    """Subscription-Heavy User 1: Many streaming services"""
    return UserProfile(
        profile_id="sub_heavy_1",
        persona=Persona.SUBSCRIPTION_HEAVY,
        income_annual=75000,
        income_quartile=3,
        payroll_frequency='biweekly',
        accounts=['checking', 'credit_card'],
        recurring_payments=[
            RecurringPayment(
                merchant_name='Rent Payment',
                amount=-1800.0,
                day_of_month=1,
                account_subtype='checking',
                category_primary='Bills',
                category_detailed='Rent',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Netflix',
                amount=-14.99,
                day_of_month=5,
                account_subtype='credit_card',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Hulu',
                amount=-12.99,
                day_of_month=6,
                account_subtype='credit_card',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Disney+',
                amount=-10.99,
                day_of_month=7,
                account_subtype='credit_card',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Spotify',
                amount=-9.99,
                day_of_month=8,
                account_subtype='credit_card',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Apple Music',
                amount=-9.99,
                day_of_month=9,
                account_subtype='credit_card',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Gym Membership',
                amount=-50.0,
                day_of_month=15,
                account_subtype='credit_card',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Software Subscription',
                amount=-29.99,
                day_of_month=20,
                account_subtype='credit_card',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
        ],
        spending_patterns=[
            SpendingPattern(
                category_primary='Food and Drink',
                category_detailed='Groceries',
                frequency_per_month=4,
                amount_range=(-150.0, -100.0),
                account_subtype='credit_card'
            ),
        ],
        credit_limit=10000.0,
        credit_balance_start=2000.0,  # 20% utilization - healthy
        credit_utilization_target=0.20,
        description="8+ subscriptions, $138/month in recurring subscriptions"
    )


# ============================================================================
# SAVINGS BUILDER PERSONA PROFILES
# ============================================================================

def create_savings_builder_profile_1() -> UserProfile:
    """Savings Builder User 1: High savings rate, low credit utilization"""
    return UserProfile(
        profile_id="savings_builder_1",
        persona=Persona.SAVINGS_BUILDER,
        income_annual=95000,
        income_quartile=4,
        payroll_frequency='biweekly',
        accounts=['checking', 'savings', 'credit_card'],
        recurring_payments=[
            RecurringPayment(
                merchant_name='Rent Payment',
                amount=-2200.0,
                day_of_month=1,
                account_subtype='checking',
                category_primary='Bills',
                category_detailed='Rent',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Savings Transfer',
                amount=-500.0,  # Regular savings contribution
                day_of_month=2,
                account_subtype='checking',
                category_primary='Transfer',
                category_detailed='Savings',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Netflix',
                amount=-14.99,
                day_of_month=10,
                account_subtype='credit_card',
                category_primary='Entertainment',
                category_detailed='Subscription',
                frequency='monthly',
                jitter_days=0
            ),
            RecurringPayment(
                merchant_name='Credit Card Payment',
                amount=-1500.0,  # Pays in full
                day_of_month=25,
                account_subtype='checking',
                category_primary='Transfer',
                category_detailed='Payment',
                frequency='monthly',
                jitter_days=1
            ),
        ],
        spending_patterns=[
            SpendingPattern(
                category_primary='Food and Drink',
                category_detailed='Groceries',
                frequency_per_month=4,
                amount_range=(-200.0, -120.0),
                account_subtype='credit_card'
            ),
            SpendingPattern(
                category_primary='Food and Drink',
                category_detailed='Restaurants',
                frequency_per_month=6,
                amount_range=(-80.0, -40.0),
                account_subtype='credit_card'
            ),
        ],
        credit_limit=15000.0,
        credit_balance_start=2000.0,  # 13% utilization - very healthy
        credit_utilization_target=0.13,
        savings_contribution_monthly=500.0,
        savings_contribution_day=2,
        description="High savings rate ($500/month), low credit utilization (13%), pays in full"
    )


# ============================================================================
# PROFILE REGISTRY
# ============================================================================

PERSONA_PROFILES = {
    Persona.HIGH_UTILIZATION: [
        create_high_utilization_profile_1,
        create_high_utilization_profile_2,
    ],
    Persona.VARIABLE_INCOME: [
        create_variable_income_profile_1,
    ],
    Persona.CREDIT_BUILDER: [
        create_credit_builder_profile_1,
    ],
    Persona.SUBSCRIPTION_HEAVY: [
        create_subscription_heavy_profile_1,
    ],
    Persona.SAVINGS_BUILDER: [
        create_savings_builder_profile_1,
    ],
}


def get_profile_templates(persona: Persona) -> List[UserProfile]:
    """Get all profile templates for a persona"""
    creators = PERSONA_PROFILES.get(persona, [])
    return [creator() for creator in creators]


def get_all_profile_templates() -> List[UserProfile]:
    """Get all profile templates"""
    all_profiles = []
    for persona in Persona:
        all_profiles.extend(get_profile_templates(persona))
    return all_profiles


# ============================================================================
# VARIATION GENERATORS FOR SCALING
# ============================================================================

# Alternative merchant names for variation
MERCHANT_VARIATIONS = {
    'Electric Company': ['Electric Company', 'Power Company', 'Utility Provider', 'Electric Utility'],
    'Internet Provider': ['Internet Provider', 'ISP', 'Cable Company', 'Internet Service'],
    'Phone Bill': ['Phone Bill', 'Mobile Service', 'Cellular Provider', 'Phone Service'],
    'Rent Payment': ['Rent Payment', 'Apartment Rent', 'Housing Payment', 'Rent'],
    'Car Payment': ['Car Payment', 'Auto Loan', 'Vehicle Payment', 'Car Loan'],
    'Gym Membership': ['Gym Membership', 'Fitness Center', 'Gym', 'Health Club'],
    'Software Subscription': ['Software Subscription', 'SaaS Subscription', 'Software Service', 'App Subscription'],
}

# Subscription merchant alternatives
SUBSCRIPTION_ALTERNATIVES = {
    'Netflix': ['Netflix'],
    'Hulu': ['Hulu'],
    'Disney+': ['Disney+'],
    'Spotify': ['Spotify', 'Apple Music', 'Pandora'],
    'Apple Music': ['Apple Music', 'Spotify', 'Pandora'],
    'Amazon Prime': ['Amazon Prime'],
    'Gym Membership': ['Gym Membership', 'Fitness Center', 'Health Club'],
    'Software Subscription': ['Software Subscription', 'Adobe Creative Cloud', 'Microsoft 365', 'SaaS Service'],
}

# Income quartile ranges
INCOME_QUARTILES = {
    1: (20000, 40000),
    2: (40000, 65000),
    3: (65000, 100000),
    4: (100000, 200000),
}


def generate_profile_variation(base_profile: UserProfile, variation_id: int) -> UserProfile:
    """Generate a variation of a base profile with realistic differences"""
    # Set seed for reproducibility but allow variation
    random.seed(hash(base_profile.profile_id + str(variation_id)) % 1000000)
    
    # Income variation within quartile
    income_min, income_max = INCOME_QUARTILES[base_profile.income_quartile]
    income_variation = random.uniform(income_min, income_max)
    
    # Rent typically 30-40% of monthly income
    monthly_income = income_variation / 12
    rent_amount = -monthly_income * random.uniform(0.30, 0.40)
    
    # Create new recurring payments with variations
    new_recurring = []
    subscription_day_counter = 5  # Start subscriptions around day 5
    
    for payment in base_profile.recurring_payments:
        # Vary merchant names
        if payment.merchant_name in MERCHANT_VARIATIONS:
            merchant_name = random.choice(MERCHANT_VARIATIONS[payment.merchant_name])
        elif payment.merchant_name in SUBSCRIPTION_ALTERNATIVES:
            merchant_name = random.choice(SUBSCRIPTION_ALTERNATIVES[payment.merchant_name])
        else:
            merchant_name = payment.merchant_name
        
        # Vary amounts slightly (±5-10%)
        amount_variation = payment.amount * random.uniform(0.90, 1.10)
        
        # Special handling for rent
        if 'rent' in payment.merchant_name.lower():
            amount_variation = rent_amount
        
        # Vary payment dates
        if payment.day_of_month > 0:
            # Keep rent on 1st, but vary others slightly
            if 'rent' in payment.merchant_name.lower():
                day_of_month = 1
            elif 'savings' in payment.merchant_name.lower() or 'transfer' in payment.merchant_name.lower():
                # Keep savings transfers on their original day (usually 2nd)
                day_of_month = payment.day_of_month
            elif 'subscription' in payment.category_detailed.lower() or payment.category_primary == 'Entertainment':
                # Space out subscriptions
                day_of_month = subscription_day_counter
                subscription_day_counter += random.randint(1, 3)
                if subscription_day_counter > 28:
                    subscription_day_counter = 5
            else:
                day_of_month = payment.day_of_month + random.randint(-2, 2)
                day_of_month = max(1, min(28, day_of_month))
        else:
            day_of_month = payment.day_of_month
        
        new_recurring.append(RecurringPayment(
            merchant_name=merchant_name,
            amount=round(amount_variation, 2),
            day_of_month=day_of_month,
            account_subtype=payment.account_subtype,
            category_primary=payment.category_primary,
            category_detailed=payment.category_detailed,
            frequency=payment.frequency,
            jitter_days=payment.jitter_days
        ))
    
    # Vary spending patterns
    new_spending = []
    for pattern in base_profile.spending_patterns:
        # Vary frequency slightly
        freq_variation = max(1, pattern.frequency_per_month + random.randint(-1, 1))
        
        # Vary amount range
        min_amount = pattern.amount_range[0] * random.uniform(0.85, 1.15)
        max_amount = pattern.amount_range[1] * random.uniform(0.85, 1.15)
        if min_amount > max_amount:
            min_amount, max_amount = max_amount, min_amount
        
        new_spending.append(SpendingPattern(
            category_primary=pattern.category_primary,
            category_detailed=pattern.category_detailed,
            frequency_per_month=freq_variation,
            amount_range=(round(min_amount, 2), round(max_amount, 2)),
            account_subtype=pattern.account_subtype,
            days_of_week=pattern.days_of_week
        ))
    
    # Vary credit card details if applicable
    credit_limit = base_profile.credit_limit
    credit_balance = base_profile.credit_balance_start
    if credit_limit:
        credit_limit = credit_limit * random.uniform(0.80, 1.20)
        if credit_balance:
            # Maintain similar utilization
            utilization = credit_balance / base_profile.credit_limit if base_profile.credit_limit else 0
            credit_balance = credit_limit * utilization * random.uniform(0.90, 1.10)
            credit_balance = min(credit_balance, credit_limit * 0.95)  # Cap at 95%
    
    # Vary savings contribution
    savings_contribution = base_profile.savings_contribution_monthly
    if savings_contribution:
        savings_contribution = savings_contribution * random.uniform(0.80, 1.20)
    
    # Vary payroll frequency slightly (but keep it realistic)
    payroll_freq = base_profile.payroll_frequency
    if random.random() < 0.2:  # 20% chance to vary
        if payroll_freq == 'biweekly':
            payroll_freq = random.choice(['biweekly', 'semi_monthly'])
        elif payroll_freq == 'semi_monthly':
            payroll_freq = random.choice(['semi_monthly', 'biweekly'])
    
    # Create new profile
    new_profile = UserProfile(
        profile_id=f"{base_profile.profile_id}_var{variation_id:02d}",
        persona=base_profile.persona,
        income_annual=round(income_variation, 2),
        income_quartile=base_profile.income_quartile,
        payroll_frequency=payroll_freq,
        accounts=base_profile.accounts.copy(),  # Keep same account types
        recurring_payments=new_recurring,
        spending_patterns=new_spending,
        credit_limit=round(credit_limit, 2) if credit_limit else None,
        credit_balance_start=round(credit_balance, 2) if credit_balance else None,
        credit_utilization_target=base_profile.credit_utilization_target,
        min_payment_only=base_profile.min_payment_only,
        savings_contribution_monthly=round(savings_contribution, 2) if savings_contribution else None,
        savings_contribution_day=base_profile.savings_contribution_day,
        description=f"Variation {variation_id} of {base_profile.description}"
    )
    
    return new_profile


def generate_users_for_persona(persona: Persona, num_users: int = 20) -> List[UserProfile]:
    """Generate multiple user profiles for a persona by creating variations of templates"""
    templates = get_profile_templates(persona)
    
    if not templates:
        raise ValueError(f"No templates found for persona: {persona}")
    
    users = []
    users_per_template = num_users // len(templates)
    remaining = num_users % len(templates)
    
    for i, template in enumerate(templates):
        # Distribute remaining users across templates
        num_variations = users_per_template + (1 if i < remaining else 0)
        
        for j in range(num_variations):
            variation = generate_profile_variation(template, j + 1)
            users.append(variation)
    
    return users


def generate_all_persona_users(users_per_persona: int = 20) -> List[UserProfile]:
    """Generate all users for all personas (100 total by default)"""
    all_users = []
    
    for persona in Persona:
        persona_users = generate_users_for_persona(persona, users_per_persona)
        all_users.extend(persona_users)
    
    return all_users

