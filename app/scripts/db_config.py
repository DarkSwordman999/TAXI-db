"""Единственное место с настройками подключения к базе TAXI.

Значения берутся из стандартных переменных PostgreSQL (PGHOST, PGPORT,
PGUSER, PGPASSWORD, PGDATABASE) — их же понимает psql в shell-скриптах.
Переменные можно задать в окружении или в файле .env в корне проекта
(образец — .env.example). Без них используются значения по умолчанию:
локальный сервер, пользователь ОС, база taxi_lab5.
"""

import getpass
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_env_file(path):
    """Читает KEY=VALUE из .env; как и в shell-скриптах, значения из .env важнее окружения."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        # через os.environ: дочерние процессы (psql, pg_dump, ./help.sh) получат те же значения
        os.environ[key.strip()] = value.strip().strip("'\"")


_load_env_file(PROJECT_ROOT / ".env")

# "or": пустая строка в .env (PGUSER=) тоже означает значение по умолчанию
DB_CONFIG = {
    "host": os.environ.get("PGHOST") or "localhost",
    "port": int(os.environ.get("PGPORT") or 5432),
    "user": os.environ.get("PGUSER") or getpass.getuser(),
    "password": os.environ.get("PGPASSWORD") or "",
    "dbname": os.environ.get("PGDATABASE") or "taxi_lab5",
}
