#!/usr/bin/env bash
# Removes everything run-demo.sh created. The label selector does the work, so
# nothing has to be listed twice -- every object above carries app=yatri-app.
set -euo pipefail

kubectl delete ingress,deploy,svc,configmap,secret -l app=yatri-app --ignore-not-found
echo
echo "remaining objects with app=yatri-app:"
kubectl get all,ingress,configmap,secret -l app=yatri-app 2>/dev/null | grep -v '^$' || echo "  none"
