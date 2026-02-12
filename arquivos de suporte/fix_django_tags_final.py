import re
import os

# Base templates directory
template_dir = r'C:\Users\Segurança\Documents\Avarias_Projeto\templates'

files = []
for root, dirs, filenames in os.walk(template_dir):
    for filename in filenames:
        if filename.endswith('.html'):
            files.append(os.path.join(root, filename))

print(f"Total templates found: {len(files)}")

for file_path in files:
    if not os.path.exists(file_path):
        continue
    print(f"Processing: {file_path}")
    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_size = len(content)

    # Fix 1: Join {{ }} tags that span multiple lines and ensure spaces
    content = re.sub(r'\{\{(.*?)\}\}', lambda m: '{{ ' + ' '.join(m.group(1).split()) + ' }}', content, flags=re.DOTALL)

    # Fix 2: Handle {% %} tags
    def fix_tag_content(match):
        inner = ' '.join(match.group(1).split())
        
        # Enforce space around comparison and math operators if they are missing
        for op in ['==', '!=', '>=', '<=', '>', '<', '+', '-', '*']:
            inner = re.sub(rf'([^\s!<>=\+\-\*\/]){re.escape(op)}([^\s!<>=\+\-\*\/])', rf'\1 {op} \2', inner)
            inner = re.sub(rf'([^\s!<>=\+\-\*\/]){re.escape(op)}\s', rf'\1 {op} ', inner)
            inner = re.sub(rf'\s{re.escape(op)}([^\s!<>=\+\-\*\/])', rf' {op} \1', inner)
        
        # Fix: Remove spaces around '/' to prevent breaking template paths
        inner = re.sub(r'\s*/\s*', '/', inner)
        
        # Fix 3: Remove spaces around '=' for assignments (but not for '==', '!=', etc.)
        inner = re.sub(r'\s*=\s*', '=', inner)
        
        # Restore spaces for comparison operators
        for op in ['==', '!=', '>=', '<=', '>', '<', '+', '-', '*']:
            inner = inner.replace(op, f' {op} ')
        
        # Final cleanup of double spaces
        inner = ' '.join(inner.split())
        
        return '{% ' + inner + ' %}'

    content = re.sub(r'\{%(.*?)%\}', fix_tag_content, content, flags=re.DOTALL)

    # Clean up double spaces near delimiters
    content = re.sub(r'\{\{ +', '{{ ', content)
    content = re.sub(r' +\}\}', ' }}', content)
    content = re.sub(r'\{% +', '{% ', content)
    content = re.sub(r' +%\}', ' %}', content)

    print(f"Fixed file size: {len(content)} bytes")

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
print("✅ Todas as tags Django foram unificadas em linhas únicas!")
print("Recarregue a página agora.")
