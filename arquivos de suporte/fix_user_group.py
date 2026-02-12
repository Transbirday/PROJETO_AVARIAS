import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

def assign_operacional(username):
    try:
        user = User.objects.get(username=username)
        group = Group.objects.get(name='Operacional')
        
        user.groups.add(group)
        print(f"User '{username}' added to group '{group.name}'.")
        
    except User.DoesNotExist:
        print(f"User '{username}' not found.")
    except Group.DoesNotExist:
        print("Group 'Operacional' not found.")

if __name__ == '__main__':
    assign_operacional('TESTE-04')
