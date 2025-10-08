#!/usr/bin/env python3

"""
Test the database and candidate loading
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database():
    try:
        from db_driver import DatabaseDriver
        
        print("🔗 Testing database connection...")
        db = DatabaseDriver()
        
        # Test getting all candidates
        candidates = db.get_all_candidates()
        print(f"📊 Found {len(candidates)} candidates in database")
        
        if candidates:
            print("\n📋 Recent candidates:")
            for i, candidate in enumerate(candidates[-3:], 1):
                print(f"  {i}. {candidate.name} ({candidate.candidate_id})")
                print(f"     Position: {candidate.position}")
                print(f"     Experience: {candidate.experience_level}")
                print(f"     Resume: {'✅' if candidate.resume_path else '❌'}")
                print(f"     Skills: {'✅' if candidate.skills else '❌'}")
                print(f"     Summary: {candidate.resume_summary[:100]}..." if candidate.resume_summary else "     Summary: ❌")
                print()
            
            # Test getting most recent candidate
            recent = db.get_most_recent_candidate()
            if recent:
                print(f"🎯 Most recent candidate: {recent.name} - {recent.position}")
                
                # Test the API function
                print("\n🧪 Testing API load_recent_candidate function...")
                try:
                    from api import AssistantFnc
                    assistant = AssistantFnc()
                    print(f"✅ API AssistantFnc initialized successfully")
                    
                except Exception as e:
                    print(f"❌ API test failed: {e}")
            else:
                print("❌ No recent candidate found")
        else:
            print("❌ No candidates found. Upload a resume first!")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database()