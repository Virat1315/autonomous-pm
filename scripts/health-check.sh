#!/usr/bin/env bash
# Health check all services
set -e

SERVICES=(
  "Web Dashboard|http://localhost:3000"
  "Ticket Service|http://localhost:3001"
  "GitHub Status|http://localhost:3002"
  "Priority Service|http://localhost:3003"
  "Standup Service|http://localhost:3004"
  "Orchestrator|http://localhost:3005"
  "Slack Intake|http://localhost:3006"
)

echo "=== Autonomous PM – Service Health Check ==="
ALL_UP=true

for entry in "${SERVICES[@]}"; do
  NAME="${entry%%|*}"
  URL="${entry##*|}"/health
  if curl -sf --max-time 3 "$URL" > /dev/null 2>&1; then
    echo "  ✓ $NAME ($URL)"
  else
    echo "  ✗ $NAME ($URL) – DOWN"
    ALL_UP=false
  fi
done

echo ""
if $ALL_UP; then
  echo "All services healthy ✓"
else
  echo "Some services are down. Check docker compose logs."
  exit 1
fi
