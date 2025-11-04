#!/usr/bin/env python3
"""Check active subscriptions for each user"""

from spendsense.storage.sqlite_manager import SQLiteManager
import sqlite3
from collections import defaultdict

db_manager = SQLiteManager()
db_manager.connect()
conn = db_manager.conn
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Known subscription merchants from the generator
SUBSCRIPTION_MERCHANTS = [
    'Netflix', 'Spotify', 'Amazon Prime', 'Disney+', 'Hulu', 
    'Apple Music', 'Gym Membership', 'Streaming Service', 
    'Software Subscription', 'Newspaper', 'Annual Subscription', 
    'Insurance Premium'
]

# Get all transactions that look like subscriptions
# Subscriptions are typically recurring Entertainment category transactions
cursor.execute('''
    SELECT 
        a.user_id,
        t.merchant_name,
        t.category_primary,
        t.category_detailed,
        COUNT(*) as transaction_count,
        AVG(ABS(t.amount)) as avg_amount,
        MIN(t.date) as first_transaction,
        MAX(t.date) as last_transaction
    FROM transactions t
    JOIN accounts a ON t.account_id = a.account_id
    WHERE t.category_detailed = 'Subscription'
       OR t.merchant_name IN ('Netflix', 'Spotify', 'Amazon Prime', 'Disney+', 'Hulu', 
                              'Apple Music', 'Gym Membership', 'Streaming Service', 
                              'Software Subscription', 'Newspaper', 'Annual Subscription', 
                              'Insurance Premium')
    GROUP BY a.user_id, t.merchant_name
    ORDER BY a.user_id, t.merchant_name
''')

subscriptions_by_user = defaultdict(list)
for row in cursor.fetchall():
    user_id = row['user_id']
    merchant = row['merchant_name']
    count = row['transaction_count']
    avg_amount = row['avg_amount']
    first_date = row['first_transaction']
    last_date = row['last_transaction']
    
    subscriptions_by_user[user_id].append({
        'merchant': merchant,
        'count': count,
        'avg_amount': avg_amount,
        'first_date': first_date,
        'last_date': last_date
    })

# Display results
print('Active Subscriptions by User')
print('=' * 80)
print()

for user_id in sorted(subscriptions_by_user.keys()):
    subs = subscriptions_by_user[user_id]
    print(f'{user_id}: {len(subs)} subscription(s)')
    for sub in subs:
        print(f'  • {sub["merchant"]:30s} - ${sub["avg_amount"]:6.2f}/mo - {sub["count"]} transactions (from {sub["first_date"]} to {sub["last_date"]})')
    print()

# Summary statistics
print('=' * 80)
print(f'Total users with subscriptions: {len(subscriptions_by_user)}')
total_subs = sum(len(subs) for subs in subscriptions_by_user.values())
print(f'Total unique subscription relationships: {total_subs}')
avg_subs_per_user = total_subs / len(subscriptions_by_user) if subscriptions_by_user else 0
print(f'Average subscriptions per user: {avg_subs_per_user:.2f}')

db_manager.close()

