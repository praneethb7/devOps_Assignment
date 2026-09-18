#!/usr/bin/env bash
# Brings up the whole Session 12 stack in dependency order and waits for it.
# Config objects first: a Pod that starts before its ConfigMap exists will fail
# with CreateContainerConfigError rather than waiting for it.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> config and secrets"
kubectl apply -f configmap.yaml -f secret.yaml

echo "==> workloads"
kubectl apply -f backend.yaml -f frontend.yaml

echo "==> waiting for rollouts"
kubectl rollout status deployment/yatri-backend  --timeout=120s
kubectl rollout status deployment/yatri-frontend --timeout=120s

echo "==> ingress"
kubectl apply -f ingress.yaml

echo "==> waiting for the ingress controller to assign an address"
for _ in $(seq 1 30); do
  addr=$(kubectl get ingress yatri-ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)
  [ -n "$addr" ] && break
  sleep 2
done

echo
kubectl get configmap,secret,deploy,svc,ingress -l app=yatri-app
echo
echo "ready -- ingress address: ${addr:-<pending>}"
