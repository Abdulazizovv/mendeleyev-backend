"""
Test script for multi-branch login scenario.
Tests that users with multiple branches get MULTI_BRANCH response, not tokens.
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


def test_multi_branch_login():
    """Test that user with multiple branches gets MULTI_BRANCH response"""
    client = APIClient()
    
    # Create test user (staff)
    import random
    test_phone = f"+99890{random.randint(1000000, 9999999)}"
    
    user = User.objects.create_user(
        phone_number=test_phone,
        password="Test1234!",
        first_name="Multi",
        last_name="Branch",
        is_staff=True,
        phone_verified=True
    )
    
    # Create 2 branches
    branch1 = Branch.objects.create(
        name="Branch 1",
        status=BranchStatuses.ACTIVE,
        type="school"
    )
    
    branch2 = Branch.objects.create(
        name="Branch 2",
        status=BranchStatuses.ACTIVE,
        type="school"
    )
    
    # Create memberships
    BranchMembership.objects.create(
        user=user,
        branch=branch1,
        role="teacher",
        title="Math Teacher"
    )
    
    BranchMembership.objects.create(
        user=user,
        branch=branch2,
        role="branch_admin",
        title="Admin"
    )
    
    print("=" * 60)
    print("TEST: Multi-branch user login")
    print("=" * 60)
    print(f"User: {user.phone_number} (is_staff={user.is_staff})")
    print(f"Branch 1: {branch1.name} - role: teacher")
    print(f"Branch 2: {branch2.name} - role: branch_admin")
    print()
    
    # Test 1: Login WITHOUT branch_id (should return MULTI_BRANCH)
    print("=" * 60)
    print("TEST 1: Login without branch_id")
    print("=" * 60)
    response = client.post('/api/v1/auth/login/', {
        'phone_number': test_phone,
        'password': 'Test1234!'
    })
    
    print(f"Status: {response.status_code}")
    print("-" * 60)
    
    if response.status_code == 200:
        data = response.json()
        print("Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print()
        
        # Validate
        has_state = 'state' in data
        is_multi_branch = data.get('state') == 'MULTI_BRANCH'
        has_branches = 'branches' in data
        has_access_token = 'access' in data
        
        print("-" * 60)
        print("VALIDATION:")
        print(f"✓ Has 'state' field: {has_state}")
        print(f"✓ State is MULTI_BRANCH: {is_multi_branch}")
        print(f"✓ Has 'branches' list: {has_branches}")
        print(f"✗ Should NOT have 'access' token: {not has_access_token}")
        
        if has_branches:
            print(f"✓ Number of branches: {len(data.get('branches', []))}")
            print(f"✓ Expected: 2")
        
        print()
        if is_multi_branch and has_branches and not has_access_token:
            print("✓✓✓ TEST 1 PASSED ✓✓✓")
        else:
            print("✗✗✗ TEST 1 FAILED ✗✗✗")
            if has_access_token:
                print("ERROR: Token was issued when it shouldn't be!")
    else:
        print(f"✗ Login failed with status {response.status_code}")
        print(response.json())
    
    # Test 2: Login WITH branch_id (should return tokens)
    print()
    print("=" * 60)
    print("TEST 2: Login with explicit branch_id")
    print("=" * 60)
    response2 = client.post('/api/v1/auth/login/', {
        'phone_number': test_phone,
        'password': 'Test1234!',
        'branch_id': str(branch1.id)
    })
    
    print(f"Status: {response2.status_code}")
    print("-" * 60)
    
    if response2.status_code == 200:
        data2 = response2.json()
        print("Response keys:", list(data2.keys()))
        
        has_access = 'access' in data2
        has_br = 'br' in data2
        has_br_role = 'br_role' in data2
        correct_branch = data2.get('br') == str(branch1.id)
        correct_role = data2.get('br_role') == 'teacher'
        
        print()
        print("VALIDATION:")
        print(f"✓ Has 'access' token: {has_access}")
        print(f"✓ Has 'br' field: {has_br}")
        print(f"✓ Has 'br_role' field: {has_br_role}")
        print(f"✓ Correct branch ID: {correct_branch}")
        print(f"✓ Correct role: {correct_role}")
        
        print()
        if has_access and has_br and correct_branch and correct_role:
            print("✓✓✓ TEST 2 PASSED ✓✓✓")
        else:
            print("✗✗✗ TEST 2 FAILED ✗✗✗")
    else:
        print(f"✗ Login failed with status {response2.status_code}")
    
    print()
    print("=" * 60)
    print("Test completed.")
    print("=" * 60)


def test_non_staff_multi_branch():
    """Test non-staff user with multiple branches"""
    client = APIClient()
    
    # Create test user (NON-staff)
    import random
    test_phone = f"+99890{random.randint(1000000, 9999999)}"
    
    user = User.objects.create_user(
        phone_number=test_phone,
        password="Test1234!",
        first_name="Regular",
        last_name="User",
        is_staff=False,  # NOT staff
        phone_verified=True
    )
    
    # Create 2 branches
    branch1 = Branch.objects.create(
        name="School A",
        status=BranchStatuses.ACTIVE,
        type="school"
    )
    
    branch2 = Branch.objects.create(
        name="School B",
        status=BranchStatuses.ACTIVE,
        type="school"
    )
    
    # Create memberships
    BranchMembership.objects.create(
        user=user,
        branch=branch1,
        role="student"
    )
    
    BranchMembership.objects.create(
        user=user,
        branch=branch2,
        role="student"
    )
    
    print()
    print("=" * 60)
    print("TEST 3: Non-staff user with multiple branches")
    print("=" * 60)
    print(f"User: {user.phone_number} (is_staff={user.is_staff})")
    print()
    
    response = client.post('/api/v1/auth/login/', {
        'phone_number': test_phone,
        'password': 'Test1234!'
    })
    
    print(f"Status: {response.status_code}")
    print("-" * 60)
    
    if response.status_code == 200:
        data = response.json()
        is_multi_branch = data.get('state') == 'MULTI_BRANCH'
        has_access = 'access' in data
        
        print(f"State: {data.get('state')}")
        print(f"Has access token: {has_access}")
        print()
        
        if is_multi_branch and not has_access:
            print("✓✓✓ TEST 3 PASSED ✓✓✓")
        else:
            print("✗✗✗ TEST 3 FAILED ✗✗✗")
    
    print("=" * 60)


if __name__ == '__main__':
    test_multi_branch_login()
    test_non_staff_multi_branch()
