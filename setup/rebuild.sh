#!/bin/bash
# Полная пересборка базы TAXI: схема и справочники, затем поездки из data/chicago/rides.
# ВНИМАНИЕ: все таблицы пересоздаются, ручные изменения в базе пропадут.
cd "$(dirname "$0")/.." || exit 1
[ -f .env ] && set -a && . ./.env && set +a
DATABASE="${PGDATABASE:-taxi}"
# в Windows Python обычно доступен только как python
PYTHON="$(command -v python3 || command -v python)"

psql -v ON_ERROR_STOP=1 -d "$DATABASE" -f setup/rebuild_database.sql || exit 1
"$PYTHON" parser/load_rides.py
