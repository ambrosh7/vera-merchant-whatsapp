#!/usr/bin/env bash
# Keep Colima + Docker bot + Cloudflare tunnel alive; refresh PUBLIC_URL.txt.
# Run in a dedicated terminal for the judge window: ./scripts/keep_public_up.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
URL_FILE="$ROOT/PUBLIC_URL.txt"
LOG="$ROOT/.tunnel.log"

start_stack() {
  if ! colima status >/dev/null 2>&1; then
    echo "$(date -u +%FT%TZ) starting colima" | tee -a "$LOG"
    colima start
  fi
  docker context use colima >/dev/null 2>&1 || true
  docker compose up -d >/dev/null
}

tunnel_ok() {
  local url="${1:-}"
  [[ -n "$url" ]] || return 1
  curl -fsS --max-time 12 "$url/v1/healthz" >/dev/null 2>&1
}

extract_url_from_log() {
  rg -o 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com' "$LOG" 2>/dev/null | tail -1 || true
}

start_tunnel() {
  pkill -f 'cloudflared tunnel --url http://127.0.0.1:8080' 2>/dev/null || true
  sleep 1
  : > "$LOG"
  echo "$(date -u +%FT%TZ) starting cloudflared" | tee -a "$LOG"
  nohup cloudflared tunnel --url http://127.0.0.1:8080 --no-autoupdate >>"$LOG" 2>&1 &
  echo $! > "$ROOT/.tunnel.pid"
  for _ in $(seq 1 40); do
    sleep 1
    url="$(extract_url_from_log)"
    if [[ -n "$url" ]] && tunnel_ok "$url"; then
      printf 'BOT_URL=%s\n\n# Auto-kept by scripts/keep_public_up.sh\n# Health: curl -fsS \"$BOT_URL/v1/healthz\"\n' "$url" > "$URL_FILE"
      echo "$(date -u +%FT%TZ) PUBLIC $url" | tee -a "$LOG"
      echo "$url"
      return 0
    fi
  done
  echo "$(date -u +%FT%TZ) tunnel failed to become healthy" | tee -a "$LOG"
  return 1
}

start_stack
CURRENT="$(rg -o 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com' "$URL_FILE" 2>/dev/null | head -1 || true)"
if ! tunnel_ok "$CURRENT"; then
  CURRENT="$(start_tunnel)"
fi

echo "Watching $CURRENT — leave this running."
while true; do
  start_stack
  if ! tunnel_ok "$CURRENT"; then
    echo "$(date -u +%FT%TZ) tunnel unhealthy — restarting" | tee -a "$LOG"
    CURRENT="$(start_tunnel)"
  fi
  sleep 45
done
