#!/usr/bin/env bash
set -e
HOST="${QUESTDB_HOST:-questdb}"
PORT="${QUESTDB_ILP_PORT:-9009}"
RETRIES=${RETRIES:-30}
SLEEP=${SLEEP:-2}

echo "Waiting for QuestDB ILP ${HOST}:${PORT} ..."
for i in $(seq 1 $RETRIES); do
  if command -v nc >/dev/null 2>&1; then
    if nc -z "$HOST" "$PORT" 2>/dev/null; then
      echo "QuestDB ILP is up. Starting Telegraf."
      exec telegraf --config /etc/telegraf/telegraf.conf
    fi
  else
    # Fallback using bash TCP if nc is unavailable
    timeout 1 bash -c "</dev/tcp/$HOST/$PORT" 2>/dev/null && {
      echo "QuestDB ILP is up. Starting Telegraf."
      exec telegraf --config /etc/telegraf/telegraf.conf
    }
  fi
  echo "Attempt $i/$RETRIES: not ready yet."
  sleep "$SLEEP"
 done

echo "QuestDB ILP not reachable after $RETRIES attempts."
exit 1
