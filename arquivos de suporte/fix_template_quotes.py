import re
import shutil

# Paths
source_file = r'C:\Users\Segurança\Documents\Avarias_Projeto\templates\app_avarias\avaria_detail_backup_before_fix.html'
target_file = r'C:\Users\Segurança\Documents\Avarias_Projeto\templates\app_avarias\avaria_detail.html'
backup_file = r'C:\Users\Segurança\Documents\Avarias_Projeto\templates\app_avarias\avaria_detail_backup_BEFORE_QUOTE_FIX.html'

# Backup current file
shutil.copy2(target_file, backup_file)
print(f"✓ Backup criado: {backup_file}")

# Read source
with open(source_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"✓ Arquivo lido: {len(content)} bytes")

# Fix all double quotes in Django filters to single quotes
# Pattern: |filter:"value" -> |filter:'value'
patterns_fixed = 0

# Fix date filters
content_new = re.sub(r'\|date:"([^"]+)"', r"|date:'\1'", content)
patterns_fixed += len(re.findall(r'\|date:"([^"]+)"', content))

# Fix default filters  
content_new = re.sub(r'\|default:"([^"]+)"', r"|default:'\1'", content_new)
patterns_fixed += len(re.findall(r'\|default:"([^"]+)"', content))

print(f"✓ Padrões corrigidos: {patterns_fixed}")

# Write to target
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(content_new)

print(f"✓ Arquivo salvo: {target_file}")
print(f"✓ Tamanho final: {len(content_new)} bytes")
print("\n✅ Template corrigido com sucesso!")
print("Por favor, recarregue a página no navegador (Ctrl+Shift+R)")
