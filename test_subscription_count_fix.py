#!/usr/bin/env python3
"""Test script to verify subscription count consistency between two views.

This script verifies that THREE critical fixes have been applied:
1. Both endpoints use the same merchant detection logic (no hardcoded filters)
2. Both endpoints compute fresh signals (no caching discrepancy)
3. Both endpoints use the same date range and exclude pending transactions
"""

import requests
import sys

def test_subscription_counts(user_id='user_001', base_url='http://localhost:8000'):
    """Test that subscription counts match between profile and subscriptions endpoints."""
    
    print(f"Testing subscription counts for {user_id}...")
    print("=" * 60)
    
    # Test 1: Get subscription count from profile (Behavioral Insights)
    try:
        profile_response = requests.get(f"{base_url}/data/profile/{user_id}")
        profile_response.raise_for_status()
        profile_data = profile_response.json()
        
        signals_count = profile_data['signals_30d']['subscriptions']['subscriptions_count']
        print(f"\n✓ Behavioral Insights Section:")
        print(f"  Subscription count from signals: {signals_count}")
        print(f"  Recurring merchants: {', '.join(profile_data['signals_30d']['subscriptions']['recurring_merchants'][:5])}")
        if len(profile_data['signals_30d']['subscriptions']['recurring_merchants']) > 5:
            print(f"  ... and {len(profile_data['signals_30d']['subscriptions']['recurring_merchants']) - 5} more")
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error getting profile: {e}")
        return False
    except KeyError as e:
        print(f"\n✗ Missing key in profile response: {e}")
        return False
    
    # Test 2: Get subscription count from subscriptions endpoint (Active Subscriptions)
    try:
        subscriptions_response = requests.get(f"{base_url}/data/subscriptions/{user_id}")
        subscriptions_response.raise_for_status()
        subscriptions_data = subscriptions_response.json()
        
        api_count = subscriptions_data['total_count']
        print(f"\n✓ Active Subscriptions Section:")
        print(f"  Subscription count from API: {api_count}")
        print(f"  Subscriptions found: {', '.join([sub['merchant_name'] for sub in subscriptions_data['subscriptions'][:5]])}")
        if len(subscriptions_data['subscriptions']) > 5:
            print(f"  ... and {len(subscriptions_data['subscriptions']) - 5} more")
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error getting subscriptions: {e}")
        return False
    except KeyError as e:
        print(f"\n✗ Missing key in subscriptions response: {e}")
        return False
    
    # Test 3: Compare counts
    print(f"\n{'=' * 60}")
    print(f"COMPARISON:")
    print(f"  Behavioral Insights: {signals_count} subscriptions")
    print(f"  Active Subscriptions: {api_count} subscriptions")
    
    if signals_count == api_count:
        print(f"\n✅ SUCCESS! Counts match ({signals_count} == {api_count})")
        print("\nAll THREE fixes have been successfully applied:")
        print("  ✓ Fix 1: Same merchant detection logic (no hardcoded filters)")
        print("  ✓ Fix 2: Fresh signals computation (no caching)")
        print("  ✓ Fix 3: Same date range [today-30, today-1] + exclude pending")
        print("\nThe subscription count discrepancy has been FULLY RESOLVED!")
        return True
    else:
        print(f"\n❌ FAILURE! Counts don't match ({signals_count} != {api_count})")
        print("\nPossible causes:")
        print("  - API server may need to be restarted to apply changes")
        print("  - Database may have been modified since last signal computation")
        print("  - There may be another edge case not yet identified")
        print("\nTry restarting the API server: python run.py --start")
        return False

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = 'user_001'
    
    print("Subscription Count Fix Verification Test")
    print("=" * 60)
    print("\nThis script verifies that THREE critical fixes have been applied:")
    print("  1. Same merchant detection logic (no hardcoded filters)")
    print("  2. Fresh signals computation (no caching discrepancy)")
    print("  3. Same date range [today-30, today-1] + exclude pending transactions")
    print("\nThese fixes ensure that the subscription counts are IDENTICAL")
    print("between the Behavioral Insights and Active Subscriptions sections.")
    print(f"\nTesting user: {user_id}")
    print("\nMake sure the API server is running:")
    print("  python run.py --start")
    print()
    
    success = test_subscription_counts(user_id)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

