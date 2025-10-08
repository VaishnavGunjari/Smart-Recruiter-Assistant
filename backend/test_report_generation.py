#!/usr/bin/env python3
"""
Test the actual interview report generation with real database
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from api import AssistantFnc, CandidateDetails
from db_driver import DatabaseDriver
import asyncio

async def test_report_generation():
    """Test generating an actual interview report"""
    print("🧪 TESTING REAL INTERVIEW REPORT GENERATION")
    print("=" * 60)
    
    # Initialize components
    assistant = AssistantFnc()
    db = DatabaseDriver()
    
    try:
        # Load the most recent candidate
        print("📋 Loading most recent candidate...")
        recent_candidate = db.get_most_recent_candidate()
        
        if not recent_candidate:
            print("❌ No candidates found. Please upload a resume first!")
            return
            
        print(f"✅ Found candidate: {recent_candidate.name}")
        print(f"   Position: {recent_candidate.position}")
        print(f"   ID: {recent_candidate.candidate_id}")
        
        # Load candidate into assistant
        assistant._candidate_details = {
            CandidateDetails.CANDIDATE_ID: recent_candidate.candidate_id,
            CandidateDetails.NAME: recent_candidate.name,
            CandidateDetails.POSITION: recent_candidate.position,
            CandidateDetails.EXPERIENCE_LEVEL: recent_candidate.experience_level,
            CandidateDetails.EMAIL: recent_candidate.email,
            CandidateDetails.PHONE: recent_candidate.phone,
            CandidateDetails.INTERVIEW_STATUS: recent_candidate.interview_status
        }
        
        # Check for existing interview data
        print("\n📊 Checking interview data...")
        interview_questions = db.get_interview_questions(recent_candidate.candidate_id)
        
        if not interview_questions:
            print("⚠️  No interview questions found. Adding sample data...")
            
            # Add some sample interview data for testing
            sample_qa = [
                ("Hi! Can you introduce yourself?", "Hi, I'm a software developer with 3 years experience in full-stack development."),
                ("Tell me about a project you're proud of", "I built an e-commerce platform that handles thousands of users with 99.9% uptime."),
                ("What technologies did you use?", "React, Node.js, MongoDB, Redis, and AWS for the infrastructure."),
                ("What's your biggest achievement?", "Leading a microservices migration that improved performance by 60%.")
            ]
            
            for question, answer in sample_qa:
                db.save_interview_question(
                    recent_candidate.candidate_id,
                    question,
                    answer,
                    8,  # Sample score
                    "Good technical response"
                )
            
            print(f"✅ Added {len(sample_qa)} sample Q&A pairs")
        else:
            print(f"✅ Found {len(interview_questions)} existing interview questions")
        
        # Generate the report
        print("\n🤖 Generating LLM analysis report...")
        print("   (This may take a few seconds...)")
        
        try:
            report = await assistant.generate_interview_report(None)
            
            print("\n📊 GENERATED INTERVIEW REPORT:")
            print("=" * 80)
            print(report)
            print("=" * 80)
            
            if "Error" not in report and len(report) > 100:
                print("\n✅ SUCCESS: Interview report generated successfully!")
                print("📝 Report length:", len(report), "characters")
            else:
                print("\n⚠️  Report generated but may be basic/fallback version")
                
        except Exception as e:
            print(f"\n❌ Error generating report: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_report_generation())