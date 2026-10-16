#!/usr/bin/env bash
# End-to-end smoke test against a running stack (compose, minikube or EKS).
# Usage: BASE_URL=http://localhost:3000 scripts/smoke-test.sh
set -euo pipefail
BASE="${BASE_URL:-http://localhost:3000}"
pass() { printf '  \033[32m✔\033[0m %s\n' "$1"; }

echo "Smoke testing $BASE"
curl -fsS "$BASE/healthz" >/dev/null && pass "frontend healthz"
curl -fsS "$BASE/api/tickets/stats" | grep -q '"total"' && pass "stats endpoint"

ID=$(curl -fsS -X POST "$BASE/api/tickets" -H 'Content-Type: application/json' \
  -d '{"subject":"Smoke test ticket","requester":"smoke@example.com","priority":"LOW","category":"OTHER"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
pass "create ticket #$ID"

curl -fsS -X PUT "$BASE/api/tickets/$ID" -H 'Content-Type: application/json' -d '{"status":"RESOLVED"}' \
  | grep -q '"RESOLVED"' && pass "update ticket"
curl -fsS -X POST "$BASE/api/tickets/$ID/comments" -H 'Content-Type: application/json' \
  -d '{"author":"smoke","body":"resolved by smoke test"}' >/dev/null && pass "add comment"
curl -fsS "$BASE/api/tickets/$ID" | grep -q '"comment_count":1' && pass "comment counted"
[[ "$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "$BASE/api/tickets/$ID")" == "204" ]] && pass "delete ticket"
[[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/tickets/$ID")" == "404" ]] && pass "ticket gone"
echo "All smoke tests passed"
