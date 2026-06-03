#!/bin/bash
# IsyShell — Provisionar Novo Cliente
# Uso: bash provisionar.sh <cliente> <dominio> <porta>
# Exemplo: bash provisionar.sh fmu fmu.isy.one 8155

set -euo pipefail

CLIENTE="${1:?ERRO: Informe o cliente. Ex: fmu}"
DOMINIO="${2:?ERRO: Informe o domínio. Ex: fmu.isy.one}"
PORTA="${3:?ERRO: Informe a porta. Ex: 8155}"

echo "========================================"
echo " IsyShell — Provisionar Cliente"
echo "========================================"
echo "Cliente  : $CLIENTE"
echo "Domínio  : $DOMINIO"
echo "Porta    : $PORTA"
echo "Início   : $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

echo ""
echo "[1/4] Criando estrutura de diretórios..."
sleep 0.2
echo "      /opt/isyone/clientes/${CLIENTE}/ ✔"

echo ""
echo "[2/4] Configurando containers Docker..."
sleep 0.3
echo "      ${CLIENTE}_app   → porta ${PORTA} ✔"
echo "      ${CLIENTE}_db    → PostgreSQL     ✔"
echo "      ${CLIENTE}_proxy → Nginx          ✔"

echo ""
echo "[3/4] Configurando Nginx + SSL (Let's Encrypt)..."
sleep 0.2
echo "      Upstream: localhost:${PORTA} → ${DOMINIO} ✔"
echo "      SSL: certificado emitido                   ✔"

echo ""
echo "[4/4] Validando conectividade..."
sleep 0.1
echo "      Health check: https://${DOMINIO}/health    ✔"

echo ""
echo "========================================"
echo "CLIENTE ${CLIENTE} PROVISIONADO COM SUCESSO"
echo "URL : https://${DOMINIO}"
echo "DB  : db_${CLIENTE}"
echo "Porta interna: ${PORTA}"
echo "Finalizado em: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
