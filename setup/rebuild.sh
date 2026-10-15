#!/bin/bash
# Полная пересборка базы TAXI: схема и справочники, затем поездки из data/chicago/rides.
# ВНИМАНИЕ: все таблицы пересоздаются, ручные изменения в базе пропадут.
cd "$(dirname "$0")/.." || exit 1
[ -f .env ] && set -a && . ./.env && set +a
DATABASE="${PGDATABASE:-taxi}"

psql -v ON_ERROR_STOP=1 -d "$DATABASE" -f setup/rebuild_database.sql || exit 1
python3 parser/load_rides.py
