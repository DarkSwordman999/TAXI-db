#!/bin/bash
# Полная пересборка базы TAXI: схема и справочники, затем поездки из data/chicago/rides.
# ВНИМАНИЕ: все таблицы пересоздаются, ручные изменения в базе пропадут.
cd "$(dirname "$0")/.." || exit 1
[ -f .env ] && set -a && . ./.env && set +a
DATABASE="${PGDATABASE:-taxi}"
PYTHON=python3
# в Windows python3 бывает заглушкой Microsoft Store, которая не запускается
"$PYTHON" -c "" 2>/dev/null || PYTHON=python

psql -v ON_ERROR_STOP=1 -d "$DATABASE" -f setup/rebuild_database.sql || exit 1
"$PYTHON" parser/load_rides.py
