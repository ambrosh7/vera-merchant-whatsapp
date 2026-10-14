#!/usr/bin/env bash
# Free public URL via Colima + Docker + Cloudflare quick tunnel.
# Keep this process running for the whole judge window.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! colima status >/dev/null 2>&1; then
  echo "Starting Colima..."
  colima start
fi

docker context use colima >/dev/null 2>&1 || true
docker compose up -d --build

echo "Waiting for local healthz..."
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8080/v1/healthz >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -fsS http://127.0.0.1:8080/v1/healthz | python3 -m json.tool

echo ""
echo "Starting Cloudflare tunnel (leave this running)..."
echo "When the URL prints, use it as BOT_URL for the judge."
echo ""
exec cloudflared tunnel --url http://127.0.0.1:8080 --no-autoupdate
