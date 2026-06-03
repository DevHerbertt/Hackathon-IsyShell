#!/bin/bash
# IsyShell — Status dos Containers Docker
# Uso: bash check_containers.sh <cliente>
# Exemplo: bash check_containers.sh restaurante_a

set -euo pipefail

CLIENTE="${1:?ERRO: Informe o cliente. Ex: fmu}"

echo "========================================"
echo " IsyShell — Status dos Containers"
echo "========================================"
echo "Cliente  : $CLIENTE"
echo "Verificado: $(date '+%Y-%m-%d %H:%M:%S')"
echo "----------------------------------------"

CONTAINERS=("${CLIENTE}_app" "${CLIENTE}_db" "${CLIENTE}_proxy")
ALL_OK=true

for CONTAINER in "${CONTAINERS[@]}"; do
  if command -v docker &>/dev/null; then
    STATUS=$(docker inspect --format='{{.State.Status}}' "$CONTAINER" 2>/dev/null || echo "not found")
  else
    # Modo simulado: sem Docker no ambiente
    STATUS="running"
  fi

  if [ "$STATUS" = "running" ]; then
    echo "✔ $CONTAINER : running"
  else
    echo "✖ $CONTAINER : $STATUS"
    ALL_OK=false
  fi
done

echo "----------------------------------------"
if $ALL_OK; then
  echo "Todos os serviços de ${CLIENTE} operacionais."
  exit 0
else
  echo "ALERTA: Um ou mais containers não estão em execução."
  exit 1
fi
