#!/usr/bin/env python3
"""Test script for Phase 3: Persona System"""

import sqlite3
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.personas.assignment import PersonaAssigner

def test_phase3():
    """Test Phase 3 persona assignment"""
    print("Testing Phase 3: Persona System\n")
    
    # Connect to database
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        assigner = PersonaAssigner(db_manager.conn)
        
        # Test with sample users
        cursor = db_manager.conn.cursor()
        cursor.execute("SELECT user_id FROM users LIMIT 10")
        test_users = [row['user_id'] for row in cursor.fetchall()]
        
        print(f"Testing persona assignment with {len(test_users)} users:\n")
        
        persona_counts = {}
        
        for user_id in test_users:
            print(f"\n{'='*60}")
            print(f"User: {user_id}")
            print(f"{'='*60}")
            
            # Assign persona
            assignment = assigner.assign_and_save(user_id)
            
            persona_name = assignment['persona_name']
            priority = assignment['priority_level']
            strength = assignment['signal_strength']
            
            print(f"Assigned Persona: {persona_name}")
            print(f"Priority Level: {priority}")
            print(f"Signal Strength: {strength:.2f}")
            
            # Count personas
            persona_counts[persona_name] = persona_counts.get(persona_name, 0) + 1
            
            # Show decision trace
            import json
            trace = json.loads(assignment['decision_trace'])
            print(f"Decision Reason: {trace.get('reason', 'unknown')}")
            if 'all_matched_personas' in trace:
                print(f"All Matched: {', '.join(trace['all_matched_personas'])}")
        
        print(f"\n{'='*60}")
        print("Persona Distribution:")
        print(f"{'='*60}")
        for persona, count in sorted(persona_counts.items(), key=lambda x: -x[1]):
            print(f"  {persona}: {count} users ({count/len(test_users)*100:.1f}%)")
        
        print(f"\n{'='*60}")
        print("Phase 3 Test Complete!")
        print(f"{'='*60}\n")
        
    finally:
        db_manager.close()

if __name__ == '__main__':
    test_phase3()

