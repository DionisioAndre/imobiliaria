# Guia de Setup Rápido - Imobiliário API

## 🚀 Setup Inicial (5 minutos)

### 1. Pré-requisitos
```bash
# Verificar Python
python --version  # Deve ser 3.8+

# Verificar PostgreSQL
psql --version

# Verificar Redis
redis-cli --version
```

### 2. Instalação Rápida
```bash
# 1. Clonar e entrar no diretório
git clone <repo-url>
cd imobiliario

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar ambiente
cp .env.example .env
# Editar .env com suas configurações

# 5. Configurar banco de dados
# Criar database no PostgreSQL:
# CREATE DATABASE imobiliario_db;

# 6. Rodar migrations
python manage.py makemigrations
python manage.py migrate

# 7. Criar superusuário
python manage.py createsuperuser

# 8. Iniciar servidor
python manage.py runserver
```

### 3. Verificar Instalação
- Acesse: http://localhost:8000/api/docs/
- Faça login no admin: http://localhost:8000/admin/

## 🧪 Testes Básicos

### Criar Usuários de Teste
```python
# No shell Django: python manage.py shell

from django.contrib.auth import get_user_model
User = get_user_model()

# Criar vendedor
vendor = User.objects.create_user(
    username='vendedor_teste',
    email='vendedor@teste.com',
    password='teste123',
    first_name='Vendedor',
    last_name='Teste',
    user_type='vendor',
    phone='+244923123456',
    province='Luanda',
    municipality='Cacuaco',
    neighborhood='Boa Esperança'
)

# Criar cliente
client = User.objects.create_user(
    username='cliente_teste',
    email='cliente@teste.com',
    password='teste123',
    first_name='Cliente',
    last_name='Teste',
    user_type='client',
    phone='+244923654321',
    province='Luanda',
    municipality='Cacuaco',
    neighborhood='Camama'
)
```

### Testar API
```bash
# 1. Login como vendedor
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "vendedor@teste.com", "password": "teste123"}'

# 2. Criar imóvel (usando token do login)
curl -X POST http://localhost:8000/api/listings/create/ \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Casa de Luxo em Luanda",
    "description": "Casa moderna com 4 quartos...",
    "property_type": "luxury_house",
    "transaction_type": "sale",
    "price": 150000000,
    "province": "Luanda",
    "municipality": "Cacuaco",
    "neighborhood": "Boa Esperança",
    "bedrooms": 4,
    "bathrooms": 3,
    "area_m2": 350.50
  }'
```

## 🔧 Configurações Adicionais

### Celery (Processo em Background)
```bash
# Terminal 1: Worker
celery -A imobiliario worker --loglevel=info

# Terminal 2: Beat Scheduler
celery -A imobiliario beat --loglevel=info

# Terminal 3: Flower (monitoramento)
pip install flower
celery -A imobiliario flower
```

### PostgreSQL Setup
```sql
-- Criar usuário e database
CREATE USER imobiliario_user WITH PASSWORD 'senha_forte';
CREATE DATABASE imobiliario_db OWNER imobiliario_user;
GRANT ALL PRIVILEGES ON DATABASE imobiliario_db TO imobiliario_user;
```

### Redis Setup
```bash
# Instalar Redis
# Ubuntu/Debian:
sudo apt-get install redis-server

# macOS:
brew install redis

# Windows:
# Baixar de https://github.com/microsoftarchive/redis/releases

# Iniciar Redis
redis-server
```

## 🚀 Deploy Produção

### 1. Configurações de Produção
```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['seu-dominio.com']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# Static files
STATIC_ROOT = '/var/www/imobiliario/static/'
MEDIA_ROOT = '/var/www/imobiliario/media/'
```

### 2. Gunicorn + Nginx
```bash
# Instalar Gunicorn
pip install gunicorn

# Criar arquivo gunicorn.service
sudo nano /etc/systemd/system/gunicorn.service

# Iniciar Gunicorn
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# Configurar Nginx
sudo nano /etc/nginx/sites-available/imobiliario
sudo ln -s /etc/nginx/sites-available/imobiliario /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 3. SSL com Let's Encrypt
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com
```

## 📊 Monitoramento

### Logs
```bash
# Verificar logs
tail -f logs/django.log

# Logs do Celery
tail -f logs/celery.log
```

### Performance
```bash
# Instalar dependências
pip install django-debug-toolbar
pip install silk

# Adicionar ao INSTALLED_APPS em settings.py
'debug_toolbar',
'silk'
```

## 🔍 Troubleshooting

### Problemas Comuns

#### 1. Erro de Migrations
```bash
# Reset migrations
python manage.py migrate listings zero
python manage.py makemigrations listings
python manage.py migrate
```

#### 2. Erro de Permissão
```bash
# Corrigir permissões de arquivos
chmod 755 manage.py
chmod -R 755 media/
```

#### 3. Celery não funciona
```bash
# Verificar Redis
redis-cli ping

# Verificar worker
celery -A imobiliario inspect active
```

#### 4. Upload de arquivos não funciona
```bash
# Verificar permissões da pasta media
sudo chown -R www-data:www-data media/
sudo chmod -R 755 media/
```

## 📞 Suporte

### Logs Importantes
- `logs/django.log` - Logs da aplicação
- `logs/celery.log` - Logs do Celery
- `/var/log/nginx/error.log` - Logs do Nginx

### Comandos Úteis
```bash
# Verificar status do Django
python manage.py check --deploy

# Verificar migrations pendentes
python manage.py showmigrations

# Backup do banco
pg_dump imobiliario_db > backup.sql

# Restaurar banco
psql imobiliario_db < backup.sql
```

---

**Pronto! 🎉 Sua API Imobiliário está configurada e funcionando!**
