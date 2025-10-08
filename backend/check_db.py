#!/usr/bin/env python3

"""
Quick script to check database contents
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from db_driver import DatabaseDriver
    
    print("🔍 Checking database contents...")
    
    # Initialize database
    db = DatabaseDriver()
    
    # Get all candidates
    candidates = db.get_all_candidates()
    
    print(f"📊 Total candidates in database: {len(candidates)}")
    
    if candidates:
        print("\n📋 Recent candidates:")
        for i, candidate in enumerate(candidates[-5:], 1):  # Show last 5
            print(f"  {i}. {candidate.name} ({candidate.candidate_id})")
            print(f"     Position: {candidate.position}")
            print(f"     Experience: {candidate.experience_level}")
            print(f"     Resume: {'✅' if candidate.resume_path else '❌'}")
            print(f"     Skills: {'✅' if candidate.skills else '❌'}")
            print(f"     Created: {candidate.created_at}")
            print()
    else:
        print("❌ No candidates found in database")
        
    print("✅ Database check complete")
    
except Exception as e:
    print(f"❌ Error checking database: {e}")
    import traceback
    traceback.print_exc()