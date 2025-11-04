"""Prompt engineering for LLM-powered financial plan generation"""

from typing import Dict, Any


def build_financial_plan_prompt(
    persona_name: str,
    signals: Dict[str, Any],
    user_data: Dict[str, Any]
) -> str:
    """Build prompt for generating personalized financial plan.
    
    Args:
        persona_name: Assigned persona name
        signals: Behavioral signals dictionary
        user_data: User account and transaction summary data
        
    Returns:
        Formatted prompt string
    """
    
    # Extract key signals for context
    credit_signals = signals.get('credit', {})
    subscriptions = signals.get('subscriptions', {})
    savings = signals.get('savings', {})
    income = signals.get('income', {})
    
    # Build persona-specific context
    persona_context = _get_persona_context(persona_name, signals)
    
    prompt = f"""You are a financial advisor helping a user with their personalized financial plan. 

## User Profile
- **Persona**: {persona_name}
{persona_context}

## Financial Signals
{_format_signals(signals)}

## User Account Summary
{_format_user_data(user_data)}

## Your Task
Generate a comprehensive, personalized financial plan in JSON format with the following structure:

{{
  "plan_summary": "A 2-3 sentence overview of the user's financial situation and primary focus areas",
  "key_insights": [
    "Insight 1 about their financial behavior",
    "Insight 2 about opportunities or concerns",
    "Insight 3 about patterns or trends"
  ],
  "action_items": [
    "Specific, actionable step 1 (e.g., 'Set up automatic payment for credit card to avoid late fees')",
    "Specific, actionable step 2",
    "Specific, actionable step 3"
  ],
  "recommendations": [
    {{
      "type": "education",
      "title": "Clear, specific title (e.g., 'Understanding Credit Utilization: A Path to Better Scores')",
      "description": "2-3 sentence description of what they'll learn and why it matters",
      "rationale": "Personalized 'because' statement citing specific data (e.g., 'because your credit utilization is at 45% and reducing it to below 30% could improve your score')"
    }}
  ]
}}

## Requirements
1. Generate exactly 5 education recommendations tailored to their persona and financial signals
2. Generate exactly 3 partner offer recommendations (these should be suggestions for financial products/services, not actual offers)
3. Each recommendation must have a clear, actionable title
4. Each rationale must cite specific numbers or behaviors from their data
5. Use an empowering, supportive tone - never shaming or judgmental
6. Focus on actionable steps they can take immediately
7. Make recommendations specific to their actual financial situation

## Output Format
Return ONLY valid JSON, no additional text or markdown formatting.

Generate the financial plan now:"""

    return prompt


def _get_persona_context(persona_name: str, signals: Dict[str, Any]) -> str:
    """Get persona-specific context for prompt."""
    
    credit = signals.get('credit', {})
    subscriptions = signals.get('subscriptions', {})
    savings = signals.get('savings', {})
    income = signals.get('income', {})
    
    if persona_name == "High Utilization":
        utilization = credit.get('credit_utilization', 0.0)
        interest = credit.get('interest_charges', 0.0)
        return f"""
- **Primary Focus**: Reducing debt and credit utilization
- **Credit Utilization**: {utilization:.1f}% (target: <30%)
- **Monthly Interest Charges**: ${interest:.2f}
- **Urgency**: High - debt management is the priority"""
    
    elif persona_name == "Variable Income Budgeter":
        pay_gap = income.get('median_pay_gap_days', 0)
        buffer = income.get('cash_flow_buffer_months', 0.0)
        return f"""
- **Primary Focus**: Managing irregular income and building stability
- **Pay Gap**: {pay_gap} days between paychecks
- **Cash Flow Buffer**: {buffer:.1f} months
- **Urgency**: Medium - stability is the priority"""
    
    elif persona_name == "Credit Builder":
        return f"""
- **Primary Focus**: Building credit history and understanding credit basics
- **Credit Status**: Building or establishing credit
- **Urgency**: Low - educational focus"""
    
    elif persona_name == "Subscription-Heavy":
        count = subscriptions.get('subscriptions_count', 0)
        monthly_spend = subscriptions.get('monthly_recurring_spend', 0.0)
        return f"""
- **Primary Focus**: Optimizing subscription spending
- **Active Subscriptions**: {count}
- **Monthly Subscription Cost**: ${monthly_spend:.2f}
- **Urgency**: Medium - optimization opportunity"""
    
    elif persona_name == "Savings Builder":
        growth_rate = savings.get('savings_growth_rate', 0.0)
        monthly_inflow = savings.get('net_savings_inflow', 0.0)
        return f"""
- **Primary Focus**: Maximizing savings growth and returns
- **Savings Growth Rate**: {growth_rate:.1f}%
- **Monthly Savings Inflow**: ${monthly_inflow:.2f}
- **Urgency**: Low - growth and optimization focus"""
    
    else:
        return f"""
- **Primary Focus**: General financial wellness
- **Urgency**: Low"""


def _format_signals(signals: Dict[str, Any]) -> str:
    """Format signals for prompt."""
    lines = []
    
    credit = signals.get('credit', {})
    if credit:
        lines.append(f"- Credit Utilization: {credit.get('credit_utilization', 0):.1f}%")
        lines.append(f"- Monthly Interest Charges: ${credit.get('interest_charges', 0):.2f}")
        lines.append(f"- Minimum Payment Only: {credit.get('minimum_payment_only', False)}")
    
    subscriptions = signals.get('subscriptions', {})
    if subscriptions:
        lines.append(f"- Active Subscriptions: {subscriptions.get('subscriptions_count', 0)}")
        lines.append(f"- Monthly Subscription Spend: ${subscriptions.get('monthly_recurring_spend', 0):.2f}")
    
    savings = signals.get('savings', {})
    if savings:
        lines.append(f"- Savings Growth Rate: {savings.get('savings_growth_rate', 0):.1f}%")
        lines.append(f"- Monthly Savings Inflow: ${savings.get('net_savings_inflow', 0):.2f}")
        lines.append(f"- Emergency Fund Coverage: {savings.get('emergency_fund_months', 0):.1f} months")
    
    income = signals.get('income', {})
    if income:
        lines.append(f"- Pay Gap: {income.get('median_pay_gap_days', 0)} days")
        lines.append(f"- Cash Flow Buffer: {income.get('cash_flow_buffer_months', 0):.1f} months")
        lines.append(f"- Income Variability: {income.get('income_variability', 0):.1f}%")
    
    return "\n".join(lines) if lines else "- No significant signals detected"


def _format_user_data(user_data: Dict[str, Any]) -> str:
    """Format user data for prompt."""
    lines = []
    
    if 'account_count' in user_data:
        lines.append(f"- Total Accounts: {user_data.get('account_count', 0)}")
    
    if 'deposit_accounts' in user_data:
        lines.append(f"- Deposit Accounts (Checking/Savings): {user_data.get('deposit_accounts', 0)}")
    
    if 'credit_accounts' in user_data:
        lines.append(f"- Credit Accounts: {user_data.get('credit_accounts', 0)}")
    
    if 'total_balance' in user_data:
        lines.append(f"- Total Account Balance: ${user_data.get('total_balance', 0):.2f}")
    
    return "\n".join(lines) if lines else "- Account data available"


def build_offer_recommendations_prompt(
    persona_name: str,
    signals: Dict[str, Any],
    education_count: int = 5
) -> str:
    """Build prompt for generating partner offer recommendations.
    
    Note: This generates suggestions for offer types, not actual product offers.
    
    Args:
        persona_name: Assigned persona name
        signals: Behavioral signals dictionary
        education_count: Number of education items already generated
        
    Returns:
        Formatted prompt string
    """
    
    credit = signals.get('credit', {})
    subscriptions = signals.get('subscriptions', {})
    savings = signals.get('savings', {})
    
    prompt = f"""Based on the user's {persona_name} persona and financial signals, generate 3 partner offer recommendations.

## Financial Signals
{_format_signals(signals)}

## Offer Types to Consider
- Credit cards (balance transfer, secured, rewards)
- Savings accounts (high-yield)
- Subscription management tools
- Budgeting apps
- Debt consolidation services
- Credit monitoring services

## Output Format
Return ONLY a JSON array with exactly 3 offer recommendations:

[
  {{
    "type": "offer",
    "title": "Clear, specific offer title (e.g., 'Balance Transfer Credit Card with 0% APR')",
    "description": "2-3 sentence description of the offer and its benefits",
    "rationale": "Personalized 'because' statement citing specific data (e.g., 'because you're paying ${credit.get('interest_charges', 0):.2f}/month in interest on a {credit.get('credit_utilization', 0):.1f}% utilization rate')"
  }}
]

## Requirements
1. Generate exactly 3 offers
2. Offers must be relevant to the persona and financial signals
3. Each rationale must cite specific numbers from their data
4. Use supportive, empowering language
5. Focus on legitimate financial products/services

Return ONLY valid JSON array, no additional text:"""

    return prompt

