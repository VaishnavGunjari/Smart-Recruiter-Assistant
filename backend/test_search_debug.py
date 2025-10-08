#!/usr/bin/env python3
"""
Debug the search functionality issue
"""
from dotenv import load_dotenv
from db_driver import DatabaseDriver
import json

# Load environment variables
load_dotenv()

def test_search_debug():
    try:
        db = DatabaseDriver()
        print("✅ Database connection successful")
        
        # First, check if we have any reports in the database
        print("\n🔍 Checking all stored reports...")
        reports_result = None
        try:
            reports_result = db.supabase.table("interview_reports").select("report_id, candidate_name, position, overall_score, created_at").execute()
            if reports_result.data:
                print(f"✅ Found {len(reports_result.data)} reports in interview_reports table:")
                for report in reports_result.data:
                    print(f"   - {report['candidate_name']} | {report['position']} | Score: {report['overall_score']} | ID: {report['report_id']}")
            else:
                print("❌ No reports found in interview_reports table")
        except Exception as e:
            print(f"❌ Error accessing interview_reports table: {e}")
            
        # Check if the summary view exists and has data
        print("\n🔍 Checking interview_reports_summary view...")
        try:
            result = db.supabase.table("interview_reports_summary").select("*").execute()
            if result.data:
                print(f"✅ Found {len(result.data)} reports in interview_reports_summary view:")
                for report in result.data:
                    print(f"   - {report['candidate_name']} | {report['position']} | Score: {report['overall_score']}")
            else:
                print("❌ No reports found in interview_reports_summary view")
        except Exception as e:
            print(f"❌ Error accessing interview_reports_summary view: {e}")
            print("ℹ️  This view might not exist - search uses this view")
            
        # Test the actual search function with different parameters
        print("\n🔍 Testing search function...")
        
        # Test 1: Search with empty parameters (should return all)
        print("\n1. Testing search with no filters:")
        try:
            reports = db.search_interview_reports()
            print(f"   Result: {len(reports)} reports found")
            for report in reports[:3]:  # Show first 3
                print(f"   - {report.candidate_name} | {report.position}")
        except Exception as e:
            print(f"   ❌ Search with no filters failed: {e}")
            
        # Test 2: Search by name if we have data
        if reports_result and reports_result.data:
            candidate_name = reports_result.data[0]['candidate_name']
            print(f"\n2. Testing search by candidate name '{candidate_name}':")
            try:
                reports = db.search_interview_reports(search_query=candidate_name)
                print(f"   Result: {len(reports)} reports found")
            except Exception as e:
                print(f"   ❌ Search by name failed: {e}")
                
        # Test 3: Search by minimum score
        print("\n3. Testing search by minimum score (5):")
        try:
            reports = db.search_interview_reports(min_score=5)
            print(f"   Result: {len(reports)} reports found")
        except Exception as e:
            print(f"   ❌ Search by score failed: {e}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    test_search_debug()