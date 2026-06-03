# ── Build stage: instalar dependências ────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Runtime stage: imagem final enxuta ────────────────────────────
FROM python:3.11-slim

LABEL maintainer="IsyShell Team <infra@isy.one>"
LABEL description="IsyShell API — Orquestrador de Infraestrutura · FMU Tech 2026"

# Dependências de sistema para execução de scripts Bash
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar pacotes Python do stage de build
COPY --from=builder /install /usr/local

WORKDIR /app

# Copiar código-fonte do backend
COPY . .

# Copiar frontend (um nível acima no contexto do docker-compose)
COPY ../index.html ../styles.css /frontend/
COPY ../data.json /frontend/ 2>/dev/null || true

# Criar diretório de dados persistentes e scripts
RUN mkdir -p /data /opt/isyone/scripts

# Variáveis de ambiente padrão (sobrescreva via docker-compose ou -e)
ENV SCRIPTS_DIR=/opt/isyone/scripts \
    DB_PATH=/data/isyshell.db \
    DEFAULT_TOKEN=isy-hackathon-2026-default-token \
    EXECUTION_TIMEOUT=120

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
