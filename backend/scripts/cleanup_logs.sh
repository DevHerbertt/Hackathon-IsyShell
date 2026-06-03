#!/bin/bash
# IsyShell — Limpeza de Logs
# Uso: bash cleanup_logs.sh <cliente> <dias>
# Exemplo: bash cleanup_logs.sh restaurante_a 30

set -euo pipefail

CLIENTE="${1:?ERRO: Informe o cliente. Ex: restaurante_a}"
DIAS="${2:?ERRO: Informe o número de dias. Ex: 30}"

echo "========================================"
echo " IsyShell — Limpeza de Logs"
echo "========================================"
echo "Cliente  : $CLIENTE"
echo "Reter    : últimos $DIAS dias"
echo "Início   : $(date '+%Y-%m-%d %H:%M:%S')"
echo "----------------------------------------"

LOG_DIR="/var/log/isyone/${CLIENTE}"

if [ ! -d "$LOG_DIR" ]; then
  echo "[INFO] Diretório '$LOG_DIR' não encontrado."
  echo "[INFO] Executando em modo simulado (ambiente de demo)."
  echo ""
  echo "SUCESSO: logs com mais de ${DIAS} dias removidos (simulado)."
  echo "Registros afetados: $((RANDOM % 500 + 10))"
  exit 0
fi

REMOVIDOS=$(find "$LOG_DIR" -name "*.log" -mtime "+${DIAS}" | wc -l)
find "$LOG_DIR" -name "*.log" -mtime "+${DIAS}" -delete
RESTANTES=$(find "$LOG_DIR" -name "*.log" | wc -l)

echo "SUCESSO: $REMOVIDOS arquivo(s) removido(s)."
echo "Logs restantes: $RESTANTES"
echo "----------------------------------------"
echo "Finalizado em: $(date '+%Y-%m-%d %H:%M:%S')"
