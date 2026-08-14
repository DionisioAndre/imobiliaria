#!/usr/bin/env python3
"""
Script automatizado para deploy da API Django no cPanel
"""
import os
import sys
import subprocess
import json
from pathlib import Path

class CPanelDeployer:
    def __init__(self, config_file='deploy_config.json'):
        self.config = self.load_config(config_file)
        self.project_name = self.config.get('project_name', 'imobiliario')
        self.cpanel_user = self.config.get('cpanel_user')
        self.domain = self.config.get('domain')
        self.project_path = f'/home/{self.cpanel_user}/{self.project_name}'
        
    def load_config(self, config_file):
        """Carregar configurações do arquivo JSON"""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        return self.get_default_config()
    
    def get_default_config(self):
        """Configurações padrão"""
        return {
            'project_name': 'imobiliario',
            'cpanel_user': input('Digite seu usuário cPanel: '),
            'domain': input('Digite seu domínio: '),
            'db_name': 'imobiliario_db',
            'db_user': 'imobiliario_user',
            'admin_email': 'admin@' + input('Digite seu domínio: '),
        }
    
    def save_config(self, config_file='deploy_config.json'):
        """Salvar configurações"""
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"Configurações salvas em {config_file}")
    
    def create_production_requirements(self):
        """Criar requirements.txt para produção"""
        production_requirements = [
            'Django>=5.2,<6.1',
            'djangorestframework>=3.14,<4.0',
            'django-cors-headers>=4.3,<5.0',
            'djangorestframework-simplejwt>=5.3,<6.0',
            'Pillow>=10.1,<11.0',
            'django-filter>=24.0,<26.0',
            'python-decouple>=3.8,<4.0',
            'drf-spectacular>=0.27,<1.0',
            'mysqlclient>=2.2,<3.0',
            'gunicorn>=21.0,<22.0',
        ]
        
        with open('requirements_production.txt', 'w') as f:
            f.write('\n'.join(production_requirements))
        
        print("✅ requirements_production.txt criado")
    
    def create_passenger_wsgi(self):
        """Criar arquivo passenger_wsgi.py"""
        wsgi_content = f'''import os
import sys

# Adicionar o diretório do projeto ao Python path
project_home = '{self.project_path}'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Configurar variáveis de ambiente
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'imobiliario.settings.production')

# Importar e configurar Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
'''
        
        with open('passenger_wsgi.py', 'w') as f:
            f.write(wsgi_content)
        
        print("✅ passenger_wsgi.py criado")
    
    def create_production_env(self):
        """Criar arquivo .env para produção"""
        env_content = f'''# Configurações de Produção
DEBUG=False
ALLOWED_HOSTS={self.domain},www.{self.domain}

# Banco de Dados
DB_NAME={self.config['db_name']}
DB_USER={self.config['db_user']}
DB_PASSWORD=SUA_SENHA_DB_AQUI
DB_HOST=localhost
DB_PORT=3306

# Configurações de Email
EMAIL_HOST=smtp.{self.domain.split('.')[-2]}.{self.domain.split('.')[-1]}
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=contato@{self.domain}
EMAIL_HOST_PASSWORD=SUA_SENHA_EMAIL_AQUI
DEFAULT_FROM_EMAIL=contato@{self.domain}

# Configurações de Segurança
SECRET_KEY=GERE_UMA_NOVA_SECRET_KEY_AQUI
SECURE_SSL_REDIRECT=True

# Configurações de Cache
CACHE_LOCATION=/tmp/django_cache

# Configurações de Logs
LOG_FILE=/home/{self.cpanel_user}/logs/django.log
DJANGO_LOG_LEVEL=INFO
APP_LOG_LEVEL=INFO

# Configurações de CORS
CORS_ALLOWED_ORIGINS=https://{self.domain},https://www.{self.domain}

# Configurações de Upload
STATIC_ROOT=/home/{self.cpanel_user}/public_html/static/
MEDIA_ROOT=/home/{self.cpanel_user}/public_html/media/
MAX_IMAGE_SIZE=5242880
MAX_VIDEO_SIZE=52428800
MAX_DOCUMENT_SIZE=10485760
'''
        
        with open('.env.production', 'w') as f:
            f.write(env_content)
        
        print("✅ .env.production criado")
        print("⚠️  Lembre-se de atualizar as senhas e SECRET_KEY!")
    
    def create_htaccess(self):
        """Criar arquivo .htaccess"""
        htaccess_content = '''# Configurações para Django
Options -MultiViews
RewriteEngine On

# Redirecionar todas as requisições para Django
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /passenger_wsgi.py/$1 [QSA,L]

# Acesso direto a arquivos estáticos
RewriteRule ^static/(.*)$ /static/$1 [L]
RewriteRule ^media/(.*)$ /media/$1 [L]

# Headers de segurança
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"

# Forçar HTTPS (se SSL estiver configurado)
# RewriteCond %{HTTPS} off
# RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
'''
        
        with open('.htaccess', 'w') as f:
            f.write(htaccess_content)
        
        print("✅ .htaccess criado")
    
    def create_deploy_script(self):
        """Criar script de deploy para cPanel"""
        deploy_script = f'''#!/bin/bash
# Script de Deploy para cPanel

echo "🚀 Iniciando deploy da API Imobiliário..."

# Variáveis
PROJECT_PATH="{self.project_path}"
PYTHON_APP="{self.project_name}"
DOMAIN="{self.domain}"

echo "📁 Verificando estrutura de diretórios..."
mkdir -p /home/{self.cpanel_user}/public_html/static
mkdir -p /home/{self.cpanel_user}/public_html/media
mkdir -p /home/{self.cpanel_user}/logs
mkdir -p /tmp/django_cache

echo "🐍 Ativando aplicação Python..."
# Isso deve ser feito via interface cPanel

echo "📦 Instalando dependências..."
cd $PROJECT_PATH
pip install -r requirements_production.txt

echo "🗄️ Rodando migrations..."
python manage.py migrate

echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "👤 Criando superusuário..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@{DOMAIN}', 'Admin123!')
    print('Superusuário criado: admin / Admin123!')
else:
    print('Superusuário já existe')
EOF

echo "🔧 Ajustando permissões..."
chmod 755 /home/{self.cpanel_user}/public_html/static
chmod 755 /home/{self.cpanel_user}/public_html/media
chmod 755 /home/{self.cpanel_user}/logs

echo "✅ Deploy concluído!"
echo "🌐 Acesse sua API em: https://{DOMAIN}/api/"
echo "🔐 Admin: https://{DOMAIN}/admin/"
echo "👤 Login: admin / Admin123!"
'''
        
        with open('deploy.sh', 'w') as f:
            f.write(deploy_script)
        
        # Tornar executável
        os.chmod('deploy.sh', 0o755)
        
        print("✅ deploy.sh criado")
    
    def create_database_instructions(self):
        """Criar instruções para configuração do banco"""
        instructions = f'''# 🗄️ Configuração do Banco de Dados no cPanel

## Passos no cPanel:

### 1. Criar Banco de Dados
1. Acesse **MySQL Database Wizard**
2. **Step 1: Create Database**
   - Nome: {self.config['db_name']}
3. **Step 2: Create Database User**
   - Username: {self.config['db_user']}
   - Password: Crie uma senha forte
4. **Step 3: Add User to Database**
   - Selecione ALL PRIVILEGES
   - Clique em "Make Changes"

### 2. Atualizar .env.production
Edite o arquivo .env.production e atualize:
- DB_PASSWORD com a senha criada
- SECRET_KEY com uma chave segura

### 3. Testar Conexão
Execute no terminal cPanel:
```bash
cd {self.project_path}
python manage.py dbshell --database=default
```

## Comandos SQL Úteis:

### Criar usuário manualmente (se necessário):
```sql
CREATE USER '{self.config['db_user']}'@'localhost' IDENTIFIED BY 'sua_senha';
GRANT ALL PRIVILEGES ON {self.config['db_name']}.* TO '{self.config['db_user']}'@'localhost';
FLUSH PRIVILEGES;
```

### Backup do banco:
```bash
mysqldump -u {self.config['db_user']} -p {self.config['db_name']} > backup.sql
```
'''
        
        with open('DATABASE_SETUP.md', 'w') as f:
            f.write(instructions)
        
        print("✅ DATABASE_SETUP.md criado")
    
    def generate_secret_key(self):
        """Gerar SECRET_KEY segura"""
        import secrets
        return secrets.token_urlsafe(50)
    
    def run_all(self):
        """Executar todos os passos de preparação"""
        print("🚀 Preparando projeto para deploy no cPanel...")
        print()
        
        # Salvar configurações
        self.save_config()
        
        # Criar arquivos necessários
        self.create_production_requirements()
        self.create_passenger_wsgi()
        self.create_production_env()
        self.create_htaccess()
        self.create_deploy_script()
        self.create_database_instructions()
        
        # Gerar SECRET_KEY
        secret_key = self.generate_secret_key()
        print(f"\n🔐 Sua SECRET_KEY gerada: {secret_key}")
        print("⚠️  Adicione esta chave ao arquivo .env.production!")
        
        print("\n✅ Preparação concluída!")
        print("\n📋 Próximos passos:")
        print("1. Faça upload dos arquivos para o cPanel")
        print("2. Siga as instruções em DATABASE_SETUP.md")
        print("3. Configure a aplicação Python no cPanel")
        print("4. Execute o script deploy.sh no terminal cPanel")
        print("5. Acesse sua API! 🌐")
        
        print(f"\n📁 Arquivos criados:")
        print("- requirements_production.txt")
        print("- passenger_wsgi.py")
        print("- .env.production")
        print("- .htaccess")
        print("- deploy.sh")
        print("- DATABASE_SETUP.md")
        print("- deploy_config.json")

def main():
    """Função principal"""
    print("🚀 Deploy API Django Imobiliário para cPanel")
    print("=" * 50)
    
    deployer = CPanelDeployer()
    deployer.run_all()

if __name__ == '__main__':
    main()
