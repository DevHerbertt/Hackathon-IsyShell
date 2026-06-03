# IsyShell — Orquestrador de Infraestrutura

> **FMU Tech Hackathon 2026** · Microsserviço Python/FastAPI que converte rotinas críticas de terminal (`.sh`) em uma API segura, auditável e conteinerizada.

---

## Estrutura do Projeto

```
isyshell-frontend/
├── index.html              ← SPA frontend (vanilla JS — integrado à API)
├── styles.css              ← Tema dark terminal
├── data.json               ← Dados de referência / seed visual
│
└── backend/                ← Microsserviço Python (Clean Architecture)
    ├── domain/             ← [DOMÍNIO] Entidades e interfaces (sem frameworks)
    │   ├── entities.py     →   Script, LogAuditoria
    │   └── repositories.py →   Interfaces abstratas (ABC)
    ├── application/        ← [APLICAÇÃO] Casos de uso puros
    │   └── use_cases.py    →   8 Use Cases (Listar, Criar, Executar, Telemetria…)
    ├── infra/              ← [INFRAESTRUTURA] Implementações concretas
    │   ├── database.py     →   SQLAlchemy + SQLite (WAL mode)
    │   ├── models.py       →   ORM models (ScriptModel, LogAuditoriaModel, ConfigModel)
    │   ├── repositories.py →   Implementações concretas dos repositórios
    │   ├── script_executor.py → subprocess.run() isolado
    │   ├── security.py     →   Autenticação X-Isy-Token + sanitização anti-CI
    │   ├── deps.py         →   Fábricas de Use Cases (FastAPI Depends)
    │   └── routers/        →   Controladores HTTP
    │       ├── scripts.py       GET/POST/PATCH/DELETE /api/v1/scripts
    │       ├── execution.py     POST /api/v1/scripts/{id}/execute
    │       ├── logs.py          GET /api/v1/logs
    │       ├── admin.py         PUT /api/v1/admin/token
    │       └── ai_telemetry.py  GET /api/v1/ai/telemetry
    ├── scripts/            ← Scripts .sh de exemplo (montados via volume)
    │   ├── cleanup_logs.sh
    │   ├── check_containers.sh
    │   └── provisionar.sh
    ├── main.py             ← Entry point FastAPI (lifespan + routers + frontend)
    ├── config.py           ← Settings via pydantic-settings / .env
    ├── requirements.txt
    ├── Dockerfile
    ├── docker-compose.yml
    └── .env.example
```

---

## Pré-requisitos

| Ferramenta | Versão mínima |
|---|---|
| Python | 3.11+ |
| pip | qualquer |
| Docker + Docker Compose | v2+ (apenas para deploy) |
| Bash | qualquer (para executar os `.sh`) |

---

## Rodando Localmente

### 1. Configurar ambiente Python

```bash
cd isyshell-frontend/backend

# Criar e ativar virtualenv
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows PowerShell

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente (opcional)

```bash
cp .env.example .env
# Edite .env conforme necessário
```

Variáveis disponíveis:

| Variável | Padrão | Descrição |
|---|---|---|
| `SCRIPTS_DIR` | `/opt/isyone/scripts` | Diretório dos scripts `.sh` |
| `DB_PATH` | `./isyshell.db` | Caminho do banco SQLite |
| `DEFAULT_TOKEN` | `isy-hackathon-2026-default-token` | Token inicial de autenticação |
| `EXECUTION_TIMEOUT` | `120` | Timeout máximo de execução (segundos) |

### 3. Iniciar o servidor

```bash
# Na raiz do projeto (isyone/)
uvicorn main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

A API sobe em `http://localhost:8000`.  
O frontend (`index.html`) é servido automaticamente em `http://localhost:8000/`.  
A documentação interativa Swagger fica em `http://localhost:8000/docs`.

### 4. Scripts de exemplo (desenvolvimento local)

Copie os scripts de demonstração para o diretório configurado:

```bash
# Linux/Mac
sudo mkdir -p /opt/isyone/scripts
sudo cp backend/scripts/*.sh /opt/isyone/scripts/
sudo chmod +x /opt/isyone/scripts/*.sh

# Ou use o diretório local alterando SCRIPTS_DIR no .env:
# SCRIPTS_DIR=./backend/scripts
```

---

## Rodando via Docker

### Build e start com Docker Compose

```bash
cd isyshell-frontend/backend

docker compose up --build -d
```

Isso cria:
- Container `isyshell-api` expondo a porta `8000`
- Volume `isyshell-data` para persistência do banco SQLite
- Volume bind-mount de `./scripts/` → `/opt/isyone/scripts` (somente-leitura)

### Verificar status

```bash
docker compose ps
docker compose logs -f isyshell
```

### Parar

```bash
docker compose down
```

### Volume de scripts em produção

Para apontar para o diretório real de scripts do host, edite `docker-compose.yml`:

```yaml
volumes:
  - /opt/isyone/scripts:/opt/isyone/scripts:ro   # ← diretório real do host
```

---

## Referência de Endpoints e Exemplos cURL

> Substitua `SEU_TOKEN` pelo token configurado (padrão: `isy-hackathon-2026-default-token`).

### Health Check (público — sem autenticação)

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "version": "2.0.0",
  "runtime": "Python 3.11 + FastAPI",
  "database": "SQLite (SQLAlchemy)",
  "scripts_dir": "/opt/isyone/scripts"
}
```

---

### GET /api/v1/scripts — Listar scripts

```bash
curl http://localhost:8000/api/v1/scripts \
  -H "X-Isy-Token: SEU_TOKEN"
```

```json
[
  {
    "id": 1,
    "name": "Limpeza de Logs",
    "filename": "cleanup_logs.sh",
    "description": "Remove logs de cupons com mais de N dias do servidor do cliente.",
    "parameters_hint": "[cliente] [dias]",
    "is_active": true,
    "created_at": "2026-06-02T10:00:00"
  }
]
```

---

### POST /api/v1/scripts — Cadastrar script

```bash
curl -X POST http://localhost:8000/api/v1/scripts \
  -H "X-Isy-Token: SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Backup Banco",
    "filename": "backup_db.sh",
    "description": "Realiza backup do banco de dados do cliente.",
    "parameters_hint": "[cliente]",
    "is_active": true
  }'
```

---

### PATCH /api/v1/scripts/{id} — Ativar ou Desativar

```bash
# Desativar script de id 1
curl -X PATCH http://localhost:8000/api/v1/scripts/1 \
  -H "X-Isy-Token: SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

---

### DELETE /api/v1/scripts/{id} — Remover

```bash
curl -X DELETE http://localhost:8000/api/v1/scripts/1 \
  -H "X-Isy-Token: SEU_TOKEN"
# HTTP 204 No Content
```

---

### POST /api/v1/scripts/{id}/execute — Executar script (frontend)

```bash
curl -X POST http://localhost:8000/api/v1/scripts/3/execute \
  -H "X-Isy-Token: SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"params": ["fmu", "fmu.isy.one", "8155"]}'
```

```json
{
  "id": 1,
  "script_name": "Provisionar Cliente",
  "status": "success",
  "output": "CLIENTE fmu PROVISIONADO COM SUCESSO\nURL: https://fmu.isy.one\nDB: db_fmu",
  "error": "",
  "duration_ms": 842,
  "executed_at": "2026-06-02T10:30:00"
}
```

---

### POST /api/v1/maintenance/execute — Executar script (spec hackathon)

```bash
curl -X POST http://localhost:8000/api/v1/maintenance/execute \
  -H "X-Isy-Token: SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"script_id": 1, "params": ["restaurante_a", "30"]}'
```

---

### GET /api/v1/logs — Histórico de auditoria

```bash
curl "http://localhost:8000/api/v1/logs?limit=50" \
  -H "X-Isy-Token: SEU_TOKEN"
```

```json
[
  {
    "id": 12,
    "script_id": 3,
    "script_name": "Provisionar Cliente",
    "params": "[\"fmu\", \"fmu.isy.one\", \"8155\"]",
    "status": "success",
    "output": "CLIENTE fmu PROVISIONADO COM SUCESSO\n...",
    "error": "",
    "duration_ms": 842,
    "executed_at": "2026-06-02T10:30:00"
  }
]
```

---

### PUT /api/v1/admin/token — Alterar token dinamicamente

```bash
curl -X PUT http://localhost:8000/api/v1/admin/token \
  -H "X-Isy-Token: SEU_TOKEN_ATUAL" \
  -H "Content-Type: application/json" \
  -d '{"token": "novo-token-super-seguro-2026"}'
```

```json
{ "message": "Token atualizado com sucesso." }
```

> O novo token passa a valer **imediatamente**, sem reiniciar o servidor.

---

### GET /api/v1/ai/telemetry — Endpoint para Agente de IA

```bash
curl http://localhost:8000/api/v1/ai/telemetry \
  -H "X-Isy-Token: SEU_TOKEN"
```

```json
{
  "summary": {
    "total_executions": 47,
    "success_count": 41,
    "error_count": 5,
    "timeout_count": 1,
    "success_rate_pct": 87.23,
    "avg_duration_ms": 1240
  },
  "scripts_ranking": [
    { "script_name": "Limpeza de Logs",    "executions": 22, "success_rate_pct": 95.45 },
    { "script_name": "Status dos Containers","executions": 15, "success_rate_pct": 80.0 },
    { "script_name": "Provisionar Cliente", "executions": 10, "success_rate_pct": 90.0 }
  ],
  "recent_history": [
    {
      "id": 47,
      "script_name": "Limpeza de Logs",
      "status": "success",
      "duration_ms": 340,
      "params_summary": "restaurante_a 30",
      "executed_at": "2026-06-02T10:30:00"
    }
  ],
  "health_score": 87.23,
  "generated_at": "2026-06-02T10:35:00",
  "context_for_llm": "IsyShell Infrastructure Orchestrator | Telemetria gerada: 2026-06-02T10:35:00 | Total execuções: 47 | Taxa de sucesso: 87.23% | Tempo médio de resposta: 1240ms | Scripts mais utilizados: Limpeza de Logs, Status dos Containers, Provisionar Cliente."
}
```

---

## Arquitetura em Camadas — Como Protege o Sistema

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (index.html)       SPA Vanilla JS             │
│  Comunica via HTTP · Header X-Isy-Token em toda chamada │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP/JSON
┌─────────────────────────▼───────────────────────────────┐
│  INFRA — FastAPI Routers + Middlewares                  │
│  · verify_token() valida X-Isy-Token contra o BD        │
│  · sanitize_params() bloqueia Command Injection         │
│  · CORS configurado / logs de acesso automáticos        │
└─────────────────────────┬───────────────────────────────┘
                          │ Calls Use Cases
┌─────────────────────────▼───────────────────────────────┐
│  APPLICATION — Casos de Uso                             │
│  · Orquestra regras sem saber de FastAPI ou SQLAlchemy  │
│  · ScriptInactiveError, ScriptNotFoundError, etc.       │
│  · ExecutarScriptUseCase valida estado antes de rodar   │
└──────────┬──────────────────────────┬───────────────────┘
           │ Repository interfaces    │ ScriptExecutor
┌──────────▼──────────┐   ┌──────────▼───────────────────┐
│  DOMAIN             │   │  INFRA — Script Executor      │
│  · Script           │   │  subprocess.run() isolado     │
│  · LogAuditoria     │   │  timeout rigoroso (120s)      │
│  · Interfaces ABC   │   │  captura stdout + stderr      │
└──────────┬──────────┘   └──────────────────────────────┘
           │ Implementações concretas
┌──────────▼──────────────────────────────────────────────┐
│  INFRA — SQLite (SQLAlchemy)                            │
│  · ScriptModel, LogAuditoriaModel, ConfigModel          │
│  · WAL mode para concorrência                           │
│  · Token persiste em tabela config (chave "api_token")  │
└─────────────────────────────────────────────────────────┘
```

### Por que essa separação protege o sistema?

| Camada | Responsabilidade | O que fica isolado |
|---|---|---|
| **Domain** | Regras de negócio puras | Não conhece HTTP, SQL ou OS |
| **Application** | Orquestração de use cases | Não sabe se é FastAPI, CLI ou testes |
| **Infra/Segurança** | Autenticação e sanitização | Token dinâmico no BD, não hardcoded |
| **Infra/Executor** | subprocess isolado | Único ponto de contato com o OS |
| **Infra/Routers** | Contrato HTTP | Traduz HTTP ↔ Use Cases |

**Proteção contra Command Injection:**  
A função `sanitize_params()` aplica uma **allowlist rígida** via regex `^[a-zA-Z0-9_\-\./@:]{1,255}$` antes de qualquer parâmetro chegar ao `subprocess.run()`. Qualquer caractere de controle shell (`;`, `|`, `&`, `$`, `` ` ``, `>`, `<`, `'`, `"`, etc.) causa rejeição imediata com HTTP 400.

**Token dinâmico:**  
O token NÃO é variável de ambiente estática. É armazenado na tabela `config` do SQLite e validado a cada requisição via `ConfigRepository.get_token()`. A rota `PUT /api/v1/admin/token` permite rotação em produção sem restart.

**Isolamento do frontend legado:**  
O SPA é servido como arquivo estático pelo próprio FastAPI (`StaticFiles`). Toda comunicação passa pela camada de segurança — o frontend nunca executa scripts diretamente.

---

## Segurança — Resumo dos 5 Pilares

| Pilar | Implementação |
|---|---|
| 🔐 Autenticação | Header `X-Isy-Token` obrigatório em todas as rotas protegidas |
| 🛡️ Token dinâmico | Armazenado no BD · trocável via API sem restart |
| 🚫 Anti-injection | Allowlist regex antes de qualquer `subprocess.run()` |
| 📋 Auditoria | Cada execução persiste: horário, script, params, stdout, stderr, duração |
| 📦 Container | Imagem `python:3.11-slim` · scripts montados via volume (`:ro`) |
