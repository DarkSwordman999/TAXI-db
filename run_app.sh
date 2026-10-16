#!/bin/bash

# папка app рядом со скриптом: проект можно положить куда угодно
cd "$(dirname "$0")/app" || exit 1
PYTHON=python3
# в Windows python3 бывает заглушкой Microsoft Store, которая не запускается
"$PYTHON" -c "" 2>/dev/null || PYTHON=python

if [ ! -f "gui.py" ]; then
    echo "Не найден app/gui.py"
    exit 1
fi

"$PYTHON" -m py_compile gui.py || exit 1
"$PYTHON" gui.py
