#!/usr/bin/env python3
"""
Test the search functionality
"""
from db_driver import DatabaseDriver

def test_search():
    try:
        db = DatabaseDriver()
        print("✅ Database connection successful")
        
        # Test if interview_reports table exists
        try:
            reports = db.search_interview_reports('test')
            print(f"✅ Interview reports table exists, found {len(reports)} reports")
        except Exception as e:
            print(f"❌ Interview reports table error: {e}")
            
        # Test if candidates exist
        try:
            candidates = db.get_all_candidates()
            print(f"✅ Found {len(candidates)} candidates")
            for candidate in candidates[-3:]:  # Show last 3
                print(f"   - {candidate.name} ({candidate.candidate_id})")
        except Exception as e:
            print(f"❌ Candidates table error: {e}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    test_search()