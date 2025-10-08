#!/usr/bin/env python3
"""
Test the resume processing endpoint to debug the issue
"""
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

def test_resume_processing():
    try:
        base_url = "http://localhost:5001"
        
        print("🔍 Testing resume processing endpoint...")
        
        # Test 1: Text-based resume processing
        print("\n1. Testing text-based resume processing:")
        sample_resume_text = """
        John Doe
        Software Developer
        
        Experience:
        - 3 years as Python Developer at TechCorp
        - Built web applications using Django and React
        - Database design with PostgreSQL
        
        Skills:
        - Python, JavaScript, React, Django
        - PostgreSQL, Git, Docker
        - AWS, CI/CD
        
        Education:
        - BS Computer Science, University XYZ (2020)
        """
        
        try:
            response = requests.post(f"{base_url}/api/processResumeAndStartInterview", 
                json={
                    "resume_text": sample_resume_text,
                    "file_type": "txt",
                    "filename": "test_resume.txt"
                },
                timeout=10
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success')}")
                if data.get('success'):
                    print(f"   Candidate ID: {data.get('candidate_id')}")
                    print(f"   Name: {data.get('candidate_name')}")
                    print(f"   Position: {data.get('position')}")
                else:
                    print(f"   Error: {data.get('error')}")
            else:
                print(f"   Error Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Text processing failed: {e}")
            
        # Test 2: Check if dependencies are available
        print("\n2. Testing RAG system dependencies:")
        try:
            response = requests.get(f"{base_url}/api/health", timeout=5)
            print(f"   Health check status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            
        # Test 3: Check environment variables
        print("\n3. Testing environment configuration:")
        try:
            # Test if we can create a candidate directly
            response = requests.post(f"{base_url}/api/createCandidate", 
                json={
                    "name": "Test User",
                    "position": "Test Position",
                    "experience_level": "Mid"
                },
                timeout=5
            )
            print(f"   Create candidate status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Database connection working")
            else:
                print(f"   ❌ Database issue: {response.text}")
        except Exception as e:
            print(f"   ❌ Database test failed: {e}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_resume_processing()