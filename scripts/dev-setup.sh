#!/usr/bin/env bash
# First-time local development setup
set -e

echo "=== Autonomous PM – Dev Setup ==="

# Check Docker
if ! command -v docker &> /dev/null; then
  echo "ERROR: Docker not installed. Install from https://docs.docker.com/get-docker/"
  exit 1
fi

# Check .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example – fill in your API keys before starting"
fi

echo "Building and starting all services…"
docker compose up -d --build

echo ""
echo "Waiting for services to be ready…"
sleep 10

bash scripts/health-check.sh

echo ""
echo "=== Setup complete! ==="
echo "  Dashboard: http://localhost:3000"
echo "  Ticket API: http://localhost:3001/docs"
echo "  Orchestrator: http://localhost:3005/docs"
