import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session

# Import manually after setup
from app_avarias.models import (
    Cliente, Condutor, Veiculo, Produto, 
    CentroDistribuicao, Avaria, AvariaItem, AvariaFoto
)

User = get_user_model()

def reset_db():
    print("Iniciando limpeza do banco de dados...")
    
    # 1. Business Data
    print("- Removendo Fotos de Avarias...")
    AvariaFoto.objects.all().delete()
    
    print("- Removendo Itens de Avarias...")
    AvariaItem.objects.all().delete()
    
    print("- Removendo Avarias...")
    Avaria.objects.all().delete()
    
    print("- Removendo Centros de Distribuição...")
    CentroDistribuicao.objects.all().delete()
    
    print("- Removendo Produtos...")
    Produto.objects.all().delete()
    
    print("- Removendo Veículos...")
    Veiculo.objects.all().delete()
    
    print("- Removendo Condutores...")
    Condutor.objects.all().delete()
    
    print("- Removendo Clientes...")
    Cliente.objects.all().delete()
    
    # 2. System Data
    print("- Limpando Logs de Auditoria...")
    LogEntry.objects.all().delete()
    
    print("- Limpando Sessões Ativas...")
    Session.objects.all().delete()
    
    # 3. Users
    print("- Removendo Usuários (mantendo apenas Superusers)...")
    deleted_users, _ = User.objects.filter(is_superuser=False).delete()
    
    print("\n" + "="*40)
    print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
    print("="*40)
    print(f"Usuários deletados: {deleted_users}")
    print(f"Superusers mantidos: {User.objects.filter(is_superuser=True).count()}")
    print("="*40)

if __name__ == "__main__":
    reset_db()
