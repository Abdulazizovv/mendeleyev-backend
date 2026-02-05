"""
Test script for single branch auto-selection during login.
Run this script to verify that staff users with a single branch 
automatically get branch-scoped JWT tokens.
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.branch.models import Branch, BranchStatuses, BranchMembership
from rest_framework.test import APIClient
import json

User = get_user_model()


def test_single_branch_staff_login():
    """Test that staff user with single branch gets auto-scoped token"""
    client = APIClient()
    
    # Use unique phone number for testing
    import random
    test_phone = f"+99890{random.randint(1000000, 9999999)}"
    
    # Create test user (staff)
    user = User.objects.create_user(
        phone_number=test_phone,
        password="Test1234!",
        first_name="Test",
        last_name="User",
        is_staff=True,
        phone_verified=True
    )
    
    # Create test branch
    branch = Branch.objects.create(
        name="Qo'qon Test",
        status=BranchStatuses.ACTIVE,
        type="school"
    )
    
    # Create single membership
    membership = BranchMembership.objects.create(
        user=user,
        branch=branch,
        role="branch_admin",
        title="Admin"
    )
    
    print("=" * 60)
    print("TEST: Staff user with single branch auto-selection")
    print("=" * 60)
    print(f"User: {user.phone_number} (is_staff={user.is_staff})")
    print(f"Branch: {branch.name} ({branch.id})")
    print(f"Membership: role={membership.role}")
    print()
    
    # Attempt login without branch_id
    response = client.post('/api/v1/auth/login/', {
        'phone_number': test_phone,
        'password': 'Test1234!'
    })
    
    print(f"Login Response Status: {response.status_code}")
    print("-" * 60)
    
    if response.status_code == 200:
        data = response.json()
        print("Response Data:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
        
        # Check if tokens have branch scope
        has_br = 'br' in data
        has_br_role = 'br_role' in data
        
        print("-" * 60)
        print("VALIDATION:")
        print(f"✓ Has 'br' field: {has_br}")
        print(f"✓ Has 'br_role' field: {has_br_role}")
        
        if has_br:
            print(f"✓ Branch ID: {data['br']}")
            print(f"✓ Expected: {str(branch.id)}")
            print(f"✓ Match: {data['br'] == str(branch.id)}")
        
        if has_br_role:
            print(f"✓ Branch Role: {data['br_role']}")
            print(f"✓ Expected: {membership.role}")
            print(f"✓ Match: {data['br_role'] == membership.role}")
        
        # Now test /api/v1/auth/me/
        print()
        print("=" * 60)
        print("TEST: /api/v1/auth/me/ endpoint")
        print("=" * 60)
        
        access_token = data.get('access')
        if access_token:
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            me_response = client.get('/api/v1/auth/me/')
            
            print(f"Me Response Status: {me_response.status_code}")
            print("-" * 60)
            
            if me_response.status_code == 200:
                me_data = me_response.json()
                print("Current Branch:")
                if me_data.get('current_branch'):
                    print(json.dumps(me_data['current_branch'], indent=2, ensure_ascii=False))
                    print()
                    print("✓ current_branch is NOT null ✓")
                else:
                    print("✗ current_branch is NULL ✗")
                
                print()
                print("Memberships:")
                print(f"Count: {len(me_data.get('memberships', []))}")
                if me_data.get('memberships'):
                    print(json.dumps(me_data['memberships'][0], indent=2, ensure_ascii=False))
        
        print()
        print("=" * 60)
        if has_br and has_br_role and data['br'] == str(branch.id):
            print("✓✓✓ TEST PASSED ✓✓✓")
        else:
            print("✗✗✗ TEST FAILED ✗✗✗")
        print("=" * 60)
    
    print()
    print("Test completed. User and branch left in DB for inspection.")


if __name__ == '__main__':
    test_single_branch_staff_login()
