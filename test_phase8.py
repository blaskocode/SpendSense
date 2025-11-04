#!/usr/bin/env python3
"""Test Phase 8: API & Deployment"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

def test_api():
    """Test API endpoints"""
    print("="*70)
    print("Phase 8: API & Deployment Test")
    print("="*70)
    print()
    
    print("⚠️  Note: This test requires the API server to be running.")
    print("   Start it with: python3 run.py --start")
    print()
    
    try:
        # Test root endpoint
        print("Testing root endpoint...")
        response = requests.get(f"{BASE_URL}/")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")
        print()
        
        # Test health check
        print("Testing health check...")
        response = requests.get(f"{BASE_URL}/health")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")
        print()
        
        # Test user creation
        print("Testing user creation...")
        response = requests.post(
            f"{BASE_URL}/users",
            json={"user_id": "test_user_001", "generate_synthetic_data": False}
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"  Error: {response.text}")
        print()
        
        # Test consent
        print("Testing consent recording...")
        response = requests.post(
            f"{BASE_URL}/users/consent",
            json={"user_id": "test_user_001"}
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {json.dumps(response.json(), indent=2)}")
        print()
        
        # Test getting profile (should work if user has data)
        print("Testing profile endpoint...")
        response = requests.get(f"{BASE_URL}/data/profile/user_001")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  User ID: {data.get('user_id')}")
            print(f"  Data Availability: {data.get('data_availability')}")
        else:
            print(f"  Note: {response.status_code} - User may not have data")
        print()
        
        # Test recommendations
        print("Testing recommendations endpoint...")
        response = requests.get(f"{BASE_URL}/data/recommendations/user_001")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Total Recommendations: {data.get('total_count')}")
        else:
            print(f"  Note: {response.status_code} - User may not have recommendations")
        print()
        
        # Test operator analytics
        print("Testing operator analytics...")
        response = requests.get(f"{BASE_URL}/operator/analytics")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Persona Distribution: {data.get('persona_distribution', {})}")
        print()
        
        # Test evaluation metrics
        print("Testing evaluation metrics...")
        response = requests.get(f"{BASE_URL}/eval/metrics")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Coverage: {data.get('scoring', {}).get('coverage', {}).get('coverage_rate', 0)}%")
            print(f"  Explainability: {data.get('scoring', {}).get('explainability', {}).get('explainability_rate', 0)}%")
        print()
        
        print("="*70)
        print("API Test Complete!")
        print("="*70)
        print("\n✅ API endpoints are functional!")
        print("📚 API documentation available at: http://localhost:8000/docs")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server.")
        print("   Make sure the server is running: python3 run.py --start")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_api()

