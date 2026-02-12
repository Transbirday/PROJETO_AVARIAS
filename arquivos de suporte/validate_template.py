import os
import django
from django.conf import settings
from django.template import Template, Context, Engine

# Configure minimal settings
if not settings.configured:
    settings.configure(
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

def validate_template(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Try to parse properties
        template = Engine.get_default().from_string(content)
        print(f"SUCCESS: Template {file_path} is valid.")
    except Exception as e:
        print(f"ERROR: Template {file_path} is invalid.")
        print(e)

if __name__ == '__main__':
    validate_template('templates/app_avarias/avaria_detail.html')
