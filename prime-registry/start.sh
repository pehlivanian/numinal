#!/bin/bash
# Prime Registry — Start Script

set -e

cd "$(dirname "$0")"

# Environment (edit these or set in shell before running)
export PRIME_REGISTRY_SECRET="${PRIME_REGISTRY_SECRET:-change-me-in-production}"
export CONTRA_WEBHOOK_SECRET="${CONTRA_WEBHOOK_SECRET:-}"
export SMTP_HOST="${SMTP_HOST:-smtp.gmail.com}"
export SMTP_PORT="${SMTP_PORT:-587}"
export SMTP_USER="${SMTP_USER:-}"
export SMTP_PASS="${SMTP_PASS:-}"
export FROM_EMAIL="${FROM_EMAIL:-registry@primeregistry.io}"

mkdir -p ledger

echo "🔢 Starting Prime Registry API..."
echo "   Ledger: $(pwd)/ledger/registry.db"
echo "   API:    http://0.0.0.0:8000"
echo "   Docs:   http://localhost:8000/docs"
echo ""

uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
