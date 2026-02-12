
import os
import django
import sys

# Setup Django environment
sys.path.append(r'c:\Users\Segurança\Documents\Avarias_Projeto')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app_avarias.models import Produto

print(f"Total products: {Produto.objects.count()}")
print(f"Active products: {Produto.objects.filter(ativo=True).count()}")
print("First 5 active products:", list(Produto.objects.filter(ativo=True)[:5]))
