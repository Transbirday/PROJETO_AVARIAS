import os
import sys
import django
from django.conf import settings

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

def test_permissions():
    print("Setting up test users...")
    User = get_user_model()
    
    # Create Groups if not exist (just in case)
    gestor_group, _ = Group.objects.get_or_create(name='Gestor')
    op_group, _ = Group.objects.get_or_create(name='Operacional')

    # Create Users
    password = 'testpassword123'
    
    user_gestor, _ = User.objects.get_or_create(username='test_gestor')
    user_gestor.set_password(password)
    user_gestor.groups.clear()
    user_gestor.groups.add(gestor_group)
    user_gestor.save()
    
    user_op, _ = User.objects.get_or_create(username='test_op')
    user_op.set_password(password)
    user_op.groups.clear() # Reset
    user_op.groups.add(op_group)
    user_op.save()
    
    client = Client()
    
    print("\n--- Testing Operacional User ---")
    client.force_login(user_op)
    
    # 1. Welcome Page (Should pass)
    resp = client.get('/')
    print(f"Welcome Page Access: {resp.status_code} (Expected 200)")
    if resp.status_code == 200:
        print("PASS: Access Granted for Welcome Page")
    else:
        print(f"FAIL: Got {resp.status_code}")

    # 2. Dashboard (Should fail)
    resp = client.get('/dashboard/')
    print(f"Dashboard Access: {resp.status_code} (Expected 403)")
    if resp.status_code == 403:
        print("PASS: Access Denied for Dashboard")
    else:
        print(f"FAIL: Got {resp.status_code}")

    # 3. Avaria List (Should pass)
    resp = client.get('/avarias/')
    print(f"Avaria List Access: {resp.status_code} (Expected 200)")
    if resp.status_code == 200:
        print("PASS: Access Granted for Avaria List")
    else:
        print(f"FAIL: Got {resp.status_code}")
        
    client.logout()
    
    print("\n--- Testing Gestor User ---")
    client.force_login(user_gestor)
    
    # 1. Welcome Page (Should pass)
    resp = client.get('/')
    print(f"Welcome Page Access: {resp.status_code} (Expected 200)")
    if resp.status_code == 200:
        print("PASS: Access Granted for Welcome Page")
    else:
        print(f"FAIL: Got {resp.status_code}")

    # 2. Dashboard (Should pass)
    resp = client.get('/dashboard/')
    print(f"Dashboard Access: {resp.status_code} (Expected 200)")
    if resp.status_code == 200:
        print("PASS: Access Granted for Dashboard")
    else:
        print(f"FAIL: Got {resp.status_code}")
        
    client.logout()
    
    print("\n--- Testing Anonymous User ---")
    resp = client.get('/')
    print(f"Welcome Page Access: {resp.status_code} (Expected 302 Redirect)")
    if resp.status_code == 302:
        print("PASS: Redirected to Login")
    else:
        print(f"FAIL: Got {resp.status_code}")

if __name__ == '__main__':
    test_permissions()
