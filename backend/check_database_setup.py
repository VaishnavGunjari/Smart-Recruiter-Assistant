#!/usr/bin/env python3
"""
Check database setup and table existence
"""
import os
from dotenv import load_dotenv
from db_driver import DatabaseDriver

# Load environment variables
load_dotenv()

def check_database_setup():
    """Check if all required tables exist"""
    print("🔍 CHECKING DATABASE SETUP")
    print("=" * 40)
    
    try:
        # Initialize database
        db = DatabaseDriver()
        print("✅ Database connection successful")
        
        # Check required tables
        tables_to_check = [
            "candidates",
            "interview_questions", 
            "interview_reports"
        ]
        
        for table_name in tables_to_check:
            try:
                result = db.supabase.table(table_name).select("*").limit(1).execute()
                print(f"✅ {table_name}: exists (sample: {len(result.data)} records)")
            except Exception as e:
                print(f"❌ {table_name}: ERROR - {e}")
                
                if table_name == "interview_reports":
                    print("   → MISSING interview_reports table!")
                    print("   → Run this SQL in your Supabase SQL editor:")
                    print("   → File: database/create_interview_reports_table.sql")
        
        # Check if interview_reports_summary view exists
        try:
            result = db.supabase.table("interview_reports_summary").select("*").limit(1).execute()
            print(f"✅ interview_reports_summary view: exists (sample: {len(result.data)} records)")
        except Exception as e:
            print(f"❌ interview_reports_summary view: ERROR - {e}")
        
        print("\n📋 ENVIRONMENT VARIABLES:")
        required_env_vars = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY", 
            "GOOGLE_API_KEY"
        ]
        
        for var in required_env_vars:
            value = os.getenv(var)
            if value:
                print(f"✅ {var}: {'*' * 10}...{value[-4:]}")
            else:
                print(f"❌ {var}: NOT SET")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Make sure all tables exist (especially interview_reports)")
        print("2. Run: cd backend && python debug_report_generation.py")
        print("3. Try the end interview button again")
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_setup()