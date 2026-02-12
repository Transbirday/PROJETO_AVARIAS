import os
import django
from django.conf import settings
from django.template import Engine, Context
from app_avarias.models import Avaria

# Configure minimal settings
if not settings.configured:
    settings.configure(
        DATABASES={'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
        }},
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': ['templates'],
            'APP_DIRS': True,
        }],
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'app_avarias',
        ]
    )
    django.setup()

def debug_render():
    try:
        avaria = Avaria.objects.first()
        if not avaria:
            print("No avaria found in DB")
            return
            
        engine = Engine.get_default()
        template = engine.get_template('app_avarias/avaria_detail.html')
        
        context = Context({
            'avaria': avaria,
            'decisao_form': {},
            'devolucao_form': {},
            'finalizacao_form': {},
            'definicao_prejuizo_form': {},
            'observacao_form': {},
            'foto_form': {},
            'fotos': [],
            'cd_form': {},
            'edicao_itens_form': {},
            'transferencia_cd_form': {},
        })
        
        rendered = template.render(context)
        with open('debug_render.html', 'w', encoding='utf-8') as f:
            f.write(rendered)
        print("Render successful. Check debug_render.html")
        
        # Check if tags are still there
        if '{%' in rendered or '{{' in rendered:
            print("WARNING: Literal tags found in rendered output!")
            # Find which tags
            import re
            tags = re.findall(r'\{%.*?%\}|\{\{.*?\}\}', rendered)
            print("Unparsed tags found:", tags[:10])
        else:
            print("No literal tags found in rendered output.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    debug_render()
