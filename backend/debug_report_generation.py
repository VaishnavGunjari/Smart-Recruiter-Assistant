#!/usr/bin/env python3
"""
Debug script to check why interview reports are not being generated
"""
import asyncio
import os
import logging
from dotenv import load_dotenv
from db_driver import DatabaseDriver
from api import AssistantFnc, CandidateDetails

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_report_generation():
    """Debug the report generation process step by step"""
    print("🔍 DEBUGGING INTERVIEW REPORT GENERATION")
    print("=" * 60)
    
    try:
        # Initialize database
        db = DatabaseDriver()
        print("✅ Database connection initialized")
        
        # Check if interview_reports table exists
        print("\n📋 CHECKING DATABASE TABLES...")
        try:
            # Try to query the interview_reports table
            result = db.supabase.table("interview_reports").select("*").limit(1).execute()
            print(f"✅ interview_reports table exists with {len(result.data)} sample records")
        except Exception as e:
            print(f"❌ ERROR: interview_reports table issue: {e}")
            print("   → You need to run the SQL script to create the table!")
            print("   → File: database/create_interview_reports_table.sql")
            return
        
        # Check if candidates table has data
        print("\n👥 CHECKING CANDIDATES...")
        try:
            recent_candidate = db.get_most_recent_candidate()
            if recent_candidate:
                print(f"✅ Found recent candidate: {recent_candidate.name} ({recent_candidate.candidate_id})")
                candidate_id = recent_candidate.candidate_id
            else:
                print("❌ No candidates found in database")
                print("   → Upload a resume and start an interview first")
                return
        except Exception as e:
            print(f"❌ ERROR getting candidates: {e}")
            return
        
        # Check interview questions for this candidate
        print(f"\n❓ CHECKING INTERVIEW QUESTIONS for {candidate_id}...")
        try:
            interview_questions = db.get_interview_questions(candidate_id)
            print(f"✅ Found {len(interview_questions)} interview questions")
            
            if len(interview_questions) == 0:
                print("⚠️  WARNING: No interview questions found!")
                print("   → This is likely why reports aren't generated")
                print("   → The AI agent needs to record Q&A during interviews")
                
                # Add some sample questions for testing
                print("   → Adding sample questions for testing...")
                sample_questions = [
                    ("Tell me about your programming experience.", "I have 3 years of experience with Python and JavaScript."),
                    ("What's your most challenging project?", "I built a real-time chat application using WebSockets."),
                    ("How do you handle debugging?", "I use logging and step-through debugging to identify issues.")
                ]
                
                for question, answer in sample_questions:
                    db.save_interview_question(candidate_id, question, answer, 8, "Good response")
                    
                print(f"✅ Added {len(sample_questions)} sample Q&A pairs")
                interview_questions = db.get_interview_questions(candidate_id)
            
            # Show first few questions
            for i, qa in enumerate(interview_questions[:3]):
                print(f"   Q{i+1}: {qa.question[:60]}...")
                print(f"   A{i+1}: {qa.answer[:60]}..." if qa.answer else "   A{i+1}: (no answer)")
                
        except Exception as e:
            print(f"❌ ERROR getting interview questions: {e}")
            return
        
        # Test the report generation function
        print(f"\n🤖 TESTING REPORT GENERATION...")
        try:
            assistant_fnc = AssistantFnc()
            
            # Set up candidate details
            assistant_fnc._candidate_details = {
                CandidateDetails.CANDIDATE_ID: recent_candidate.candidate_id,
                CandidateDetails.NAME: recent_candidate.name,
                CandidateDetails.POSITION: recent_candidate.position,
                CandidateDetails.EXPERIENCE_LEVEL: recent_candidate.experience_level,
                CandidateDetails.EMAIL: recent_candidate.email,
                CandidateDetails.PHONE: recent_candidate.phone,
                CandidateDetails.INTERVIEW_STATUS: "completed"
            }
            
            print("✅ Candidate details set up")
            print(f"   Name: {recent_candidate.name}")
            print(f"   Position: {recent_candidate.position}")
            print(f"   ID: {recent_candidate.candidate_id}")
            
            # Generate the report
            print("\n🔄 Generating report (this may take a few seconds)...")
            report_result = await assistant_fnc.generate_interview_report(None)
            
            print("\n📊 REPORT GENERATION RESULT:")
            print("=" * 60)
            print(report_result)
            print("=" * 60)
            
            # Check if report was saved to database
            print(f"\n💾 CHECKING DATABASE FOR SAVED REPORT...")
            saved_report = db.get_interview_report_by_candidate(candidate_id)
            if saved_report:
                print(f"✅ Report found in database!")
                print(f"   Report ID: {saved_report.report_id}")
                print(f"   Overall Score: {saved_report.overall_score}/10")
                print(f"   Recommendation: {saved_report.hiring_recommendation}")
            else:
                print("❌ No report found in database")
                print("   → The report generation succeeded but wasn't saved")
                print("   → Check Supabase permissions or table structure")
            
        except Exception as e:
            print(f"❌ ERROR generating report: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n🎉 DEBUG COMPLETE!")
        print("   → If you see this, the report generation system is working")
        print("   → Try the end interview button again")
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_report_generation())