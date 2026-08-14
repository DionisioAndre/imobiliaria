# Imobiliário API - Plataforma de Venda e Arrendamento de Imóveis em Angola

Uma API completa e robusta construída com Django + Django REST Framework para uma plataforma de marketplace de imóveis focada no mercado angolano.

## 🏠 Características Principais

### Sistema de Usuários
- **3 tipos de usuários**: Cliente, Vendedor, Administrador
- Autenticação JWT com SimpleJWT
- Sistema de verificação de usuários
- Perfis completos com informações de localização

### Sistema de Imóveis
- **Tipos de imóveis**: Casas de luxo, Terrenos, Vivendas, Apartamentos, Casas pequenas, Quartos em bairros
- **Tipos de transação**: Venda, Arrendamento, Arrendamento curto duração
- Sistema de validação crítico (documentos, imagens, vídeos obrigatórios)
- Upload de múltiplas imagens, vídeos e documentos
- Localização detalhada com coordenadas GPS
- Sistema de status automático (ativo, expirado, vendido, arrendado)

### Sistema de Chat
- Chat isolado por imóvel e por usuário
- Suporte a mensagens de texto, imagens e arquivos
- Sistema de notificações em tempo real
- Bloqueio de usuários
- Histórico completo de conversas

### Sistema de Patrocínio (ADS)
- Pacotes de patrocínio predefinidos
- Prioridade na listagem para imóveis patrocinados
- Sistema de pagamento integrado
- Estatísticas de performance
- Controle automático de expiração

### Sistema de Contratos
- Contratos de arrendamento digitais
- Assinatura eletrônica
- Sistema de renovação
- Controle de pagamentos mensais
- Cálculo automático de multas

### Sistema de Busca Avançada
- Filtros por tipo, preço, localização, características
- Busca textual em múltiplos campos
- Ordenação inteligente (patrocinados primeiro, depois aleatória)
- Paginação otimizada

### Automação e Monitoramento
- Tarefas agendadas com Celery
- Expiração automática de imóveis
- Atualização de status de contratos
- Limpeza automática de dados antigos
- Estatísticas e relatórios

## 🛠️ Stack Tecnológico

- **Backend**: Django 4.2.16
- **API**: Django REST Framework 3.14.0
- **Autenticação**: SimpleJWT
- **Banco de Dados**: PostgreSQL
- **Tarefas Agendadas**: Celery + Redis
- **Documentação**: drf-spectacular (OpenAPI/Swagger)
- **Filtros**: django-filter
- **Upload de Arquivos**: Pillow
- **CORS**: django-cors-headers

## 📁 Estrutura do Projeto

```
imobiliario/
├── imobiliario/           # Configuração principal
│   ├── settings.py       # Configurações do Django
│   ├── urls.py          # URLs principais
│   ├── celery.py        # Configuração do Celery
│   └── wsgi.py          # WSGI config
├── users/               # App de usuários
│   ├── models.py        # Modelos de usuário
│   ├── serializers.py   # Serializers
│   ├── views.py         # Views
│   ├── permissions.py   # Permissões customizadas
│   └── urls.py          # URLs do app
├── listings/            # App de imóveis
│   ├── models.py        # Modelos de imóveis
│   ├── serializers.py   # Serializers
│   ├── views.py         # Views
│   ├── filters.py       # Filtros avançados
│   ├── tasks.py         # Tarefas Celery
│   └── urls.py          # URLs do app
├── chat/                # App de chat
│   ├── models.py        # Modelos de chat
│   ├── serializers.py   # Serializers
│   ├── views.py         # Views
│   ├── tasks.py         # Tarefas Celery
│   └── urls.py          # URLs do app
├── ads/                 # App de patrocínios
│   ├── models.py        # Modelos de patrocínio
│   ├── serializers.py   # Serializers
│   ├── views.py         # Views
│   ├── tasks.py         # Tarefas Celery
│   └── urls.py          # URLs do app
├── contracts/           # App de contratos
│   ├── models.py        # Modelos de contratos
│   ├── serializers.py   # Serializers
│   ├── views.py         # Views
│   ├── tasks.py         # Tarefas Celery
│   └── urls.py          # URLs do app
├── media/               # Uploads de arquivos
├── static/              # Arquivos estáticos
├── requirements.txt     # Dependências
└── manage.py           # Script de gerenciamento
```

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.8+
- PostgreSQL
- Redis (para Celery)
- pip

### 1. Clonar o projeto
```bash
git clone <repositório>
cd imobiliario
```

### 2. Ambiente Virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente
Criar arquivo `.env`:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=imobiliario_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

### 5. Configurar Banco de Dados
```bash
# Criar migrations
python manage.py makemigrations

# Aplicar migrations
python manage.py migrate
```

### 6. Criar Superusuário
```bash
python manage.py createsuperuser
```

### 7. Rodar Servidor
```bash
python manage.py runserver
```

### 8. Rodar Celery (em outro terminal)
```bash
# Worker
celery -A imobiliario worker --loglevel=info

# Beat scheduler
celery -A imobiliario beat --loglevel=info
```

## 📚 Documentação da API

### Endpoints Principais

#### Autenticação
- `POST /api/auth/register/` - Registro de usuário
- `POST /api/auth/login/` - Login
- `POST /api/auth/logout/` - Logout
- `GET /api/auth/profile/` - Perfil do usuário
- `PUT /api/auth/profile/` - Atualizar perfil

#### Imóveis
- `GET /api/listings/` - Listar imóveis
- `POST /api/listings/create/` - Criar imóvel
- `GET /api/listings/{id}/` - Detalhes do imóvel
- `PUT /api/listings/{id}/update/` - Atualizar imóvel
- `DELETE /api/listings/{id}/delete/` - Excluir imóvel
- `POST /api/listings/{id}/contact/` - Contatar proprietário
- `POST /api/listings/{id}/publish/` - Publicar imóvel

#### Chat
- `GET /api/chat/` - Listar chats
- `POST /api/chat/create/` - Criar chat
- `GET /api/chat/{id}/` - Detalhes do chat
- `GET /api/chat/{id}/messages/` - Mensagens do chat
- `POST /api/chat/{id}/messages/create/` - Enviar mensagem

#### Patrocínios
- `GET /api/ads/packages/` - Pacotes disponíveis
- `GET /api/ads/` - Meus patrocínios
- `POST /api/ads/create/` - Criar patrocínio
- `POST /api/ads/{id}/activate/` - Ativar patrocínio

#### Contratos
- `GET /api/contracts/` - Meus contratos
- `POST /api/contracts/create/` - Criar contrato
- `GET /api/contracts/{id}/` - Detalhes do contrato
- `POST /api/contracts/{id}/sign/` - Assinar contrato

### Documentação Interativa
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

## 🔐 Regras de Negócio

### Publicação de Imóveis
- **OBRIGATÓRIO**: Pelo menos 1 documento de titularidade
- **OBRIGATÓRIO**: Mínimo de 4 imagens
- **OBRIGATÓRIO**: 1 vídeo
- **OBRIGATÓRIO**: Descrição completa da localização
- Imóveis incompletos ficam com status "pendente"

### Sistema de Patrocínio
- Imóveis patrocinados aparecem primeiro nas buscas
- Ordenação entre patrocinados por nível de prioridade
- Após expiração, perdem prioridade automaticamente

### Sistema de Chat
- Um chat por imóvel por usuário
- Mensagens separadas por contexto
- Sistema de bloqueio para evitar spam

### Contratos de Arrendamento
- Assinatura digital obrigatória de ambas as partes
- Ativação automática após assinaturas completas
- Expiração automática ao término do contrato

## 🧪 Testes

### Rodar Testes
```bash
# Todos os testes
python manage.py test

# Testes de um app específico
python manage.py test listings

# Testes com coverage
coverage run --source='.' manage.py test
coverage report
```

## 📊 Monitoramento e Logs

### Logs
Os logs são configurados em `settings.py` e salvos em `logs/django.log`.

### Tarefas Agendadas
O sistema usa Celery para automação:
- Expiração de imóveis (a cada hora)
- Atualização de contratos (a cada 30 minutos)
- Expiração de patrocínios (a cada 30 minutos)
- Cálculo de multas (a cada hora)

## 🔧 Configurações Adicionais

### Upload de Arquivos
- **Imagens**: Máximo 5MB por imagem
- **Vídeos**: Máximo 50MB por vídeo
- **Documentos**: Máximo 10MB por documento

### Segurança
- JWT tokens com expiração configurável
- CORS configurado para frontend
- Validação de entrada em todos os endpoints
- Permissões baseadas em roles

## 🚀 Deploy

### Produção
1. Configurar `DEBUG=False`
2. Usar PostgreSQL em produção
3. Configurar servidor web (Gunicorn + Nginx)
4. Configurar Redis para Celery
5. Configurar variáveis de ambiente
6. Rodar migrations: `python manage.py migrate`
7. Coletar static files: `python manage.py collectstatic`

### Docker
O projeto pode ser containerizado com Docker e Docker Compose.

## 🤝 Contribuição

1. Fork o projeto
2. Criar branch para feature: `git checkout -b feature/nova-feature`
3. Commit mudanças: `git commit -am 'Add nova feature'`
4. Push para branch: `git push origin feature/nova-feature`
5. Abrir Pull Request

## 📝 Licença

Este projeto está licenciado sob a MIT License.

## 📞 Suporte

Para suporte, envie email para [email] ou abra uma issue no GitHub.

---

**Desenvolvido com ❤️ para o mercado imobiliário angolano**
