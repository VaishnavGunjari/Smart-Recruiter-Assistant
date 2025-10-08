#!/usr/bin/env python3
"""
Test the interview data flow to identify where Q&A is not being saved
"""
from dotenv import load_dotenv
from db_driver import DatabaseDriver
import json

# Load environment variables
load_dotenv()

def test_interview_data_flow():
    try:
        db = DatabaseDriver()
        print("✅ Database connection successful")
        
        # Check recent candidates
        print("\n🔍 Checking recent candidates...")
        recent_candidates = []
        try:
            candidates = db.get_all_candidates()
            recent_candidates = candidates[-3:] if candidates else []
            
            for candidate in recent_candidates:
                print(f"\n👤 Candidate: {candidate.name} ({candidate.candidate_id})")
                print(f"   Position: {candidate.position}")
                print(f"   Status: {candidate.interview_status}")
                print(f"   Created: {candidate.created_at[:16] if candidate.created_at else 'N/A'}")
                
                # Check interview questions for this candidate
                questions = db.get_interview_questions(candidate.candidate_id)
                print(f"   📝 Interview Questions: {len(questions)}")
                
                if questions:
                    for i, q in enumerate(questions[:2], 1):  # Show first 2 questions
                        print(f"      Q{i}: {q.question[:50]}...")
                        print(f"      A{i}: {q.answer[:50] if q.answer else '(no answer)'}...")
                else:
                    print("      ❌ No interview questions recorded")
                    
                # Check if report exists
                try:
                    report = db.get_interview_report_by_candidate(candidate.candidate_id)
                    if report:
                        print(f"   📊 Report exists: ID {report.report_id}")
                        print(f"      Overall Score: {report.overall_score}/10")
                        print(f"      Recommendation: {report.hiring_recommendation}")
                    else:
                        print("   📊 No report generated yet")
                except Exception as e:
                    print(f"   📊 Error checking report: {e}")
                    
        except Exception as e:
            print(f"❌ Error checking candidates: {e}")
            
        # Test manual Q&A saving
        print("\n🧪 Testing manual Q&A saving...")
        try:
            if recent_candidates:
                test_candidate = recent_candidates[0]
                print(f"   Using candidate: {test_candidate.name}")
                
                # Save a test question
                test_qa = db.save_interview_question(
                    test_candidate.candidate_id,
                    "Test question: What is your experience with Python?",
                    "Test answer: I have 3 years of Python development experience.",
                    8,
                    "Good technical response"
                )
                
                print(f"   ✅ Test Q&A saved with ID: {test_qa.question_id}")
                
                # Verify it was saved
                all_questions = db.get_interview_questions(test_candidate.candidate_id)
                print(f"   📝 Total questions now: {len(all_questions)}")
                
            else:
                print("   ❌ No candidates available for testing")
                
        except Exception as e:
            print(f"   ❌ Error testing Q&A saving: {e}")
            
        # Show the root cause
        print("\n🔍 ROOT CAUSE ANALYSIS:")
        print("=" * 50)
        print("""
The issue is that during live interviews, the AI agent is NOT automatically
recording questions and answers to the database.

The interview flow should be:
1. AI asks question → record question in DB
2. User responds → record answer in DB  
3. Repeat for each Q&A pair
4. At end, generate report from all Q&A data

But currently:
❌ Q&A pairs are not being saved during conversation
❌ When report generation runs, it finds no interview data
❌ Report generation fails or creates empty/basic reports

SOLUTION NEEDED:
- Modify the AI agent to automatically call record_interview_question()
- Ensure every question/answer exchange is saved to database
- Test the complete flow from interview → Q&A storage → report generation
        """)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_interview_data_flow()