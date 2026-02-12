import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from app_avarias.models import Avaria, Condutor, Veiculo, Produto, Cliente

def create_groups():
    # 1. Create Groups
    gestor_group, created = Group.objects.get_or_create(name='Gestor')
    operacional_group, created = Group.objects.get_or_create(name='Operacional')
    
    print("Groups 'Gestor' and 'Operacional' ensured.")

    # 2. Define Permissions (Optional: if we want to use strictly Django permissions later)
    # For now, we are using group-based checks in decorators/templates as per plan.
    # But it's good practice to assign model permissions just in case.
    
    # Models common to both
    models = [Avaria, Condutor, Veiculo, Produto, Cliente]
    
    for model in models:
        content_type = ContentType.objects.get_for_model(model)
        permissions = Permission.objects.filter(content_type=content_type)
        
        for perm in permissions:
            gestor_group.permissions.add(perm)
            operacional_group.permissions.add(perm)
            
    print("Basic model permissions added to both groups.")
    
    # Extra usage:
    # Gestor has access to everything.
    # Operacional has access to everything EXCEPT:
    # - Dashboard (Custom View)
    # - Definição de Prejuízo (Custom View)
    # - Global Search (Custom View)
    
    # Since these are views, not specific model permissions (unless we created custom permissions),
    # the Group check in decorators will handle it.
    
    print("Done.")

if __name__ == '__main__':
    create_groups()
