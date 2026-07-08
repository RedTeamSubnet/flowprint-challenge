#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

PORT="${FLR_API_PORT:-10001}"
BASE_URL="http://localhost:${PORT}"

echo "Checking ${BASE_URL}/ping"
curl -fsS "${BASE_URL}/ping"
echo

echo "Checking ${BASE_URL}/health"
curl -fsS "${BASE_URL}/health"
echo

echo "Healthcheck passed."
echo "Docs: ${BASE_URL}/docs"
echo "OpenAPI: ${BASE_URL}/openapi.json"
