import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

def check_user_groups(username):
    try:
        user = User.objects.get(username=username)
        print(f"User: {user.username}")
        print(f"Is Superuser: {user.is_superuser}")
        print(f"Groups: {[g.name for g in user.groups.all()]}")
        
        all_groups = Group.objects.all()
        print(f"All Groups in DB: {[g.name for g in all_groups]}")
        
    except User.DoesNotExist:
        print(f"User '{username}' not found.")

if __name__ == '__main__':
    check_user_groups('TESTE-04')
