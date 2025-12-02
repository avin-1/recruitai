import requests
import json
import time

def test_endpoint(name, url, payload, expected_action=None, expected_text=None):
    print(f"--- Testing {name} ---")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload)}")
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            success = True
            if expected_action:
                if data.get('action') == expected_action:
                    print(f"✅ Action matched: {expected_action}")
                else:
                    print(f"❌ Action mismatch. Expected: {expected_action}, Got: {data.get('action')}")
                    success = False
            
            if expected_text:
                if expected_text.lower() in data.get('message', '').lower() or expected_text.lower() in data.get('response', '').lower():
                    print(f"✅ Text matched: {expected_text}")
                else:
                    print(f"❌ Text mismatch. Expected to contain: {expected_text}")
                    success = False
            
            return success
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection refused. Is the server running on {url}?")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    print("\n")

def main():
    results = {}
    
    # 1. Test Upload Component (Port 8080)
    # Intent: Update Profile Field
    results['Upload'] = test_endpoint(
        "Upload Component (Update Field)",
        "http://localhost:8080/chat",
        {"message": "Change title to Senior Engineer", "context": {"profile": {"job_title": "Engineer"}}},
        expected_action="UPDATE_PROFILE_FIELD"
    )
    
    # 2. Test Shortlisting Component (Port 5001)
    # Intent: Create Test
    results['Shortlisting'] = test_endpoint(
        "Shortlisting Component (Create Test)",
        "http://localhost:5001/api/tests/chat",
        {"message": "Create a python test"},
        expected_action="OPEN_CREATE_TEST"
    )
    
    # 3. Test Interview Component (Port 5002)
    # Intent: Remove Candidate
    results['Interview'] = test_endpoint(
        "Interview Component (Remove Candidate)",
        "http://localhost:5002/api/interviews/chat",
        {"message": "Remove alice@example.com from the list", "hr_email": "test@example.com"},
        expected_action="REMOVE_CANDIDATE"
    )
    
    print("\n=== Summary ===")
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
            
    if all_passed:
        print("\nAll agentic flows verified successfully!")
    else:
        print("\nSome tests failed. Please check the logs.")

if __name__ == "__main__":
    main()
