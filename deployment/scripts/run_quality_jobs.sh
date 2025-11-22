#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/weihai-app}
SRC_DIR=${SRC_DIR:-$APP_DIR/src}
VENV_DIR=${VENV_DIR:-$APP_DIR/venv}
PYTHON_BIN=${PYTHON_BIN:-$VENV_DIR/bin/python}
MANAGE=${MANAGE:-$SRC_DIR/manage.py}
PROJECT_IDS=${PROJECT_IDS:-}
STAT_TYPE=${STAT_TYPE:-quality}
SKIP_ALERTS=${SKIP_ALERTS:-0}
SKIP_GLOBAL=${SKIP_GLOBAL:-0}

if [[ ! -f "$MANAGE" ]]; then
  echo "[run_quality_jobs] manage.py 不存在: $MANAGE" >&2
  exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "[run_quality_jobs] Python 解释器不可用: $PYTHON_BIN" >&2
  exit 1
fi

source "$VENV_DIR/bin/activate"

ARGS=("run_quality_jobs" "--stat-type" "$STAT_TYPE")

if [[ "$SKIP_GLOBAL" == "1" || "$SKIP_GLOBAL" == "true" ]]; then
  ARGS+=("--skip-global")
fi

if [[ -n "$PROJECT_IDS" ]]; then
  IFS=',' read -ra IDS <<<"$PROJECT_IDS"
  for id in "${IDS[@]}"; do
    trimmed=$(echo "$id" | xargs)
    if [[ -n "$trimmed" ]]; then
      ARGS+=("--project" "$trimmed")
    fi
  done
fi

if [[ "$SKIP_ALERTS" == "1" || "$SKIP_ALERTS" == "true" ]]; then
  ARGS+=("--skip-alerts")
fi

cd "$SRC_DIR"
exec "$PYTHON_BIN" "$MANAGE" "${ARGS[@]}"
