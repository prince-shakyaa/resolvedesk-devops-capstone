#!/usr/bin/env bash
# Generate sustained traffic so the HPA scales and Grafana panels fill up.
# Usage: URL=http://resolvedesk.local scripts/load-test.sh [requests] [concurrency]
set -euo pipefail

URL="${URL:-http://resolvedesk.local}"
REQUESTS="${1:-3000}"
CONCURRENCY="${2:-20}"

echo "Hitting $URL with $REQUESTS requests at concurrency $CONCURRENCY"

# Mix of reads and a few writes so several handlers show up in the dashboard.
worker() {
  for _ in $(seq 1 "$1"); do
    curl -s -o /dev/null "$URL/api/tickets" || true
    curl -s -o /dev/null "$URL/api/tickets/stats" || true
    curl -s -o /dev/null "$URL/api/tickets?status=OPEN&priority=HIGH" || true
    curl -s -o /dev/null -X POST "$URL/api/tickets" -H 'Content-Type: application/json' \
      -d '{"subject":"Load test ticket","category":"OTHER","priority":"LOW","requester":"loadtest@example.com"}' || true
  done
}

PER_WORKER=$(( REQUESTS / CONCURRENCY / 4 ))
for _ in $(seq 1 "$CONCURRENCY"); do worker "$PER_WORKER" & done
wait
echo "Done. Watch scaling with: kubectl get hpa -n resolvedesk -w"
