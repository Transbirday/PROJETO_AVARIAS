import os
import shutil

# Backup e paths
file_path = r'C:\Users\Segurança\Documents\Avarias_Projeto\templates\app_avarias\avaria_detail.html'
backup_path = r'C:\Users\Segurança\Documents\Avarias_Projeto\templates\app_avarias\avaria_detail_backup_before_fix.html'

# Criar backup
if os.path.exists(file_path):
    shutil.copy2(file_path, backup_path)
    print(f"✓ Backup criado em: {backup_path}")

# Ler arquivo atual
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Substituir caracteres problemáticos HTML entities por seus símbolos corretos
# O Django não precisa de entities HTML em templates, deve usar os símbolos diretamente
replacements = {
    '&amp;': '&',  # Corrige &amp; para &
}

original_content = content
for old, new in replacements.items():
    content = content.replace(old, new)

# Escrever arquivo corrigido
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

if content != original_content:
    print(f"✓ Arquivo corrigido!")
    print(f"✓ Total de substituições: {sum(original_content.count(old) for old in replacements.keys())}")
    print(f"✓ Linhas: {len(content.splitlines())}")
else:
    print("ℹ Nenhuma alteração necessária - template está correto")

print("\n✅ Fix aplicado com sucesso!")
print("Por favor, recarregue a página no navegador (Ctrl+F5)")
