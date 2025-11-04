"""Education content catalog"""

from typing import List, Dict
from dataclasses import dataclass

from ..personas.criteria import Persona
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class EducationItem:
    """Education content item"""
    title: str
    description: str
    category: str
    persona: str


class EducationCatalog:
    """Static education content catalog organized by persona"""
    
    def __init__(self):
        """Initialize education catalog"""
        self._catalog = self._build_catalog()
    
    def get_education_items(self, persona_name: str, count: int = 5) -> List[EducationItem]:
        """Get education items for a persona.
        
        Args:
            persona_name: Persona display name
            count: Number of items to return (default: 5)
            
        Returns:
            List of education items
        """
        items = self._catalog.get(persona_name, [])
        return items[:count]
    
    def _build_catalog(self) -> Dict[str, List[EducationItem]]:
        """Build the education content catalog"""
        catalog = {}
        
        # High Utilization
        catalog["High Utilization"] = [
            EducationItem(
                title="Avalanche vs Snowball: Debt Paydown Strategies",
                description="Compare two popular debt payoff methods to find the best approach for your situation.",
                category="Debt Management",
                persona="High Utilization"
            ),
            EducationItem(
                title="How Credit Utilization Affects Your Score",
                description="Learn how keeping your credit utilization below 30% can improve your credit score.",
                category="Credit Education",
                persona="High Utilization"
            ),
            EducationItem(
                title="Setting Up Autopay to Avoid Late Fees",
                description="Step-by-step guide to setting up automatic payments and saving on late fees.",
                category="Payment Management",
                persona="High Utilization"
            ),
            EducationItem(
                title="Balance Transfer Cards: Pros and Cons",
                description="Understand when balance transfer cards can help and when they might not be worth it.",
                category="Debt Management",
                persona="High Utilization"
            ),
            EducationItem(
                title="Creating a Debt Payoff Timeline",
                description="Build a realistic timeline to become debt-free based on your current situation.",
                category="Financial Planning",
                persona="High Utilization"
            )
        ]
        
        # Variable Income Budgeter
        catalog["Variable Income Budgeter"] = [
            EducationItem(
                title="Percent-Based Budgeting for Irregular Income",
                description="Learn to budget using percentages instead of fixed amounts when income varies.",
                category="Budgeting",
                persona="Variable Income Budgeter"
            ),
            EducationItem(
                title="Building a 3-Month Emergency Fund",
                description="Why 3 months matters for variable income earners and how to build it gradually.",
                category="Emergency Fund",
                persona="Variable Income Budgeter"
            ),
            EducationItem(
                title="Smoothing Income with Savings Buffers",
                description="Use savings to smooth out income fluctuations and maintain consistent spending.",
                category="Cash Flow",
                persona="Variable Income Budgeter"
            ),
            EducationItem(
                title="Essential vs Discretionary: Priority Spending",
                description="Identify must-have expenses and prioritize them when income is uncertain.",
                category="Budgeting",
                persona="Variable Income Budgeter"
            ),
            EducationItem(
                title="Cash Flow Forecasting Basics",
                description="Simple methods to predict your cash flow and avoid shortfalls.",
                category="Financial Planning",
                persona="Variable Income Budgeter"
            )
        ]
        
        # Credit Builder
        catalog["Credit Builder"] = [
            EducationItem(
                title="Credit 101: How Credit Works",
                description="Fundamentals of credit scores, credit reports, and how they affect your financial options.",
                category="Credit Basics",
                persona="Credit Builder"
            ),
            EducationItem(
                title="Secured Credit Cards Explained",
                description="How secured cards work and why they're a great first step to building credit.",
                category="Credit Building",
                persona="Credit Builder"
            ),
            EducationItem(
                title="Building Credit Without Going Into Debt",
                description="Smart strategies to build credit history without accumulating debt.",
                category="Credit Building",
                persona="Credit Builder"
            ),
            EducationItem(
                title="Credit Myths Debunked",
                description="Common misconceptions about credit and the truth behind them.",
                category="Credit Education",
                persona="Credit Builder"
            ),
            EducationItem(
                title="When to Use Credit vs Debit",
                description="Guidelines for choosing between credit and debit cards for different situations.",
                category="Credit Education",
                persona="Credit Builder"
            )
        ]
        
        # Subscription-Heavy
        catalog["Subscription-Heavy"] = [
            EducationItem(
                title="The $200 Subscription Audit Checklist",
                description="A systematic approach to reviewing all your subscriptions and identifying savings.",
                category="Subscription Management",
                persona="Subscription-Heavy"
            ),
            EducationItem(
                title="Negotiating Lower Bills: Scripts That Work",
                description="Proven scripts and strategies for negotiating lower subscription rates.",
                category="Subscription Management",
                persona="Subscription-Heavy"
            ),
            EducationItem(
                title="Setting Up Subscription Alerts",
                description="How to set up alerts and reminders to avoid forgotten subscriptions.",
                category="Subscription Management",
                persona="Subscription-Heavy"
            ),
            EducationItem(
                title="Free Alternatives to Paid Services",
                description="Quality free alternatives to common paid subscriptions.",
                category="Subscription Management",
                persona="Subscription-Heavy"
            ),
            EducationItem(
                title="Annual vs Monthly: The True Cost",
                description="Calculate whether annual subscriptions actually save you money.",
                category="Subscription Management",
                persona="Subscription-Heavy"
            )
        ]
        
        # Savings Builder
        catalog["Savings Builder"] = [
            EducationItem(
                title="SMART Goal Setting for Savings",
                description="Set Specific, Measurable, Achievable, Relevant, and Time-bound savings goals.",
                category="Goal Setting",
                persona="Savings Builder"
            ),
            EducationItem(
                title="Automating Savings: Set It and Forget It",
                description="How to automate your savings so you don't have to think about it.",
                category="Savings Automation",
                persona="Savings Builder"
            ),
            EducationItem(
                title="High-Yield Savings Accounts Explained",
                description="Why HYSA rates matter and how to find the best accounts.",
                category="Savings Optimization",
                persona="Savings Builder"
            ),
            EducationItem(
                title="CD Laddering for Better Returns",
                description="Advanced strategy for maximizing returns on your savings with certificates of deposit.",
                category="Savings Optimization",
                persona="Savings Builder"
            ),
            EducationItem(
                title="Emergency Fund vs Investment: What Goes Where",
                description="How to balance emergency fund needs with long-term investment goals.",
                category="Financial Planning",
                persona="Savings Builder"
            )
        ]
        
        # Welcome (for new users)
        catalog["Welcome"] = [
            EducationItem(
                title="Getting Started with Financial Planning",
                description="Basic steps to take control of your finances and build healthy habits.",
                category="Getting Started",
                persona="Welcome"
            ),
            EducationItem(
                title="Understanding Your Financial Dashboard",
                description="Learn how to read and use your SpendSense insights effectively.",
                category="Getting Started",
                persona="Welcome"
            ),
            EducationItem(
                title="Building Your First Budget",
                description="Simple budgeting strategies for beginners.",
                category="Budgeting",
                persona="Welcome"
            ),
            EducationItem(
                title="The Importance of Emergency Funds",
                description="Why emergency funds matter and how to start building one.",
                category="Emergency Fund",
                persona="Welcome"
            ),
            EducationItem(
                title="Credit Basics for Beginners",
                description="Essential credit concepts everyone should understand.",
                category="Credit Basics",
                persona="Welcome"
            )
        ]
        
        return catalog

