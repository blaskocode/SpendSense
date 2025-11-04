#!/usr/bin/env python3
"""Test script for Phase 4: Recommendation Engine"""

import sqlite3
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.recommend.engine import RecommendationEngine

def test_phase4():
    """Test Phase 4 recommendation engine"""
    print("Testing Phase 4: Recommendation Engine\n")
    
    # Connect to database
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        engine = RecommendationEngine(db_manager.conn)
        
        # Test with sample users
        cursor = db_manager.conn.cursor()
        cursor.execute("SELECT user_id FROM users LIMIT 5")
        test_users = [row['user_id'] for row in cursor.fetchall()]
        
        print(f"Testing recommendation generation with {len(test_users)} users:\n")
        
        for user_id in test_users:
            print(f"\n{'='*70}")
            print(f"User: {user_id}")
            print(f"{'='*70}")
            
            # Generate recommendations
            recommendations = engine.generate_and_save(user_id)
            
            # Separate education and offers
            education = [r for r in recommendations if r.type == 'education']
            offers = [r for r in recommendations if r.type == 'offer']
            
            print(f"\nEducation Recommendations ({len(education)}):")
            for i, rec in enumerate(education, 1):
                print(f"\n  {i}. {rec.title}")
                print(f"     Rationale: {rec.rationale[:100]}...")
            
            print(f"\nPartner Offers ({len(offers)}):")
            for i, rec in enumerate(offers, 1):
                print(f"\n  {i}. {rec.title}")
                print(f"     Rationale: {rec.rationale[:100]}...")
        
        print(f"\n{'='*70}")
        print("Phase 4 Test Complete!")
        print(f"{'='*70}\n")
        
        # Show summary
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM recommendations
            GROUP BY type
        """)
        summary = cursor.fetchall()
        print("Recommendation Summary:")
        for row in summary:
            print(f"  {row['type']}: {row['count']} recommendations")
        
    finally:
        db_manager.close()

if __name__ == '__main__':
    test_phase4()

