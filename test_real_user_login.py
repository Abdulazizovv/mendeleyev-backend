"""
Test script for real user +998901662205 to verify single branch auto-selection.
"""
import requests
import json

BASE_URL = "http://localhost:8101"  # Adjust if your port is different

def test_real_user_login():
    """Test login with real user"""
    
    print("=" * 60)
    print("Testing real user: +998901662205")
    print("=" * 60)
    print()
    
    # Login without branch_id
    print("1. Login without branch_id...")
    response = requests.post(f"{BASE_URL}/api/v1/auth/login/", json={
        "phone_number": "+998901662205",
        "password": "your_password_here"  # UPDATE THIS!
    })
    
    print(f"Status: {response.status_code}")
    print("-" * 60)
    
    if response.status_code == 200:
        data = response.json()
        print("Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
        
        has_br = 'br' in data
        has_br_role = 'br_role' in data
        
        print("-" * 60)
        print("Validation:")
        print(f"✓ Has 'br' field: {has_br}")
        print(f"✓ Has 'br_role' field: {has_br_role}")
        
        if has_br:
            print(f"✓ Branch ID: {data['br']}")
        if has_br_role:
            print(f"✓ Branch Role: {data['br_role']}")
        
        # Test /api/v1/auth/me/
        if 'access' in data:
            print()
            print("2. Testing /api/v1/auth/me/...")
            me_response = requests.get(
                f"{BASE_URL}/api/v1/auth/me/",
                headers={"Authorization": f"Bearer {data['access']}"}
            )
            
            print(f"Status: {me_response.status_code}")
            print("-" * 60)
            
            if me_response.status_code == 200:
                me_data = me_response.json()
                
                print("Current Branch:")
                if me_data.get('current_branch'):
                    print(json.dumps(me_data['current_branch'], indent=2, ensure_ascii=False))
                    print()
                    print("✓✓✓ current_branch is SET ✓✓✓")
                else:
                    print("✗✗✗ current_branch is NULL ✗✗✗")
                
                print()
                print("Memberships count:", len(me_data.get('memberships', [])))
        
        print()
        print("=" * 60)
        if has_br and has_br_role:
            print("✓✓✓ SUCCESS - Auto-selection working! ✓✓✓")
        else:
            print("✗✗✗ FAILED - br/br_role not in token ✗✗✗")
        print("=" * 60)
    else:
        print(f"✗ Login failed: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except:
            print(response.text)

if __name__ == '__main__':
    print()
    print("NOTE: Update the password in the script before running!")
    print()
    test_real_user_login()
