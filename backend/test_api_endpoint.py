#!/usr/bin/env python3
"""
Test the actual API endpoint that frontend calls
"""
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

def test_api_endpoint():
    try:
        # Test different possible ports
        possible_urls = [
            "http://localhost:5001",
            "http://127.0.0.1:5001", 
            "http://localhost:5000",
            "http://127.0.0.1:5000"
        ]
        
        working_url = None
        
        print("🔍 Finding the correct backend URL...")
        for base_url in possible_urls:
            try:
                response = requests.get(f"{base_url}/api/search-reports?min_score=1", timeout=2)
                print(f"✅ Found backend running at: {base_url}")
                working_url = base_url
                break
            except requests.exceptions.ConnectionError:
                print(f"❌ No server at {base_url}")
            except Exception as e:
                print(f"⚠️  Error testing {base_url}: {e}")
                
        if not working_url:
            print("❌ Could not find running backend server. Checked ports 5000 and 8000.")
            return
            
        print(f"\n🔍 Testing API endpoint /api/search-reports at {working_url}...")
        
        # Test 1: Search with candidate name
        print("\n1. Testing search by candidate name 'Prashanth':")
        try:
            response = requests.get(f"{working_url}/api/search-reports?q=Prashanth", timeout=5)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            
        # Test 2: Search with no filters (should return all)
        print("\n2. Testing search with no filters:")
        try:
            response = requests.get(f"{working_url}/api/search-reports?min_score=1", timeout=5)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success')}")
                print(f"   Total: {data.get('total')}")
                print(f"   Reports count: {len(data.get('reports', []))}")
            else:
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            
        # Test 3: Search by position
        print("\n3. Testing search by position 'Software Developer':")
        try:
            response = requests.get(f"{working_url}/api/search-reports?position=Software Developer", timeout=5)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Success: {data.get('success')}")
                print(f"   Total: {data.get('total')}")
                print(f"   Reports: {len(data.get('reports', []))}")
            else:
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_api_endpoint()