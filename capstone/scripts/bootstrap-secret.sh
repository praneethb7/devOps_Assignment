#!/usr/bin/env bash
set -euo pipefail
namespace="${1:-campuscrate}"
kubectl apply -f "$(dirname "$0")/../k8s/namespace.yaml"
if ! kubectl -n "$namespace" get secret campuscrate-db >/dev/null 2>&1; then
  password="$(openssl rand -hex 24)"
  kubectl -n "$namespace" create secret generic campuscrate-db \
    --from-literal=POSTGRES_PASSWORD="$password" \
    --from-literal=DATABASE_URL="postgresql+psycopg://campuscrate:$password@postgres:5432/campuscrate"
fi
