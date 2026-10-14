#!/bin/bash

# папка app рядом со скриптом: проект можно положить куда угодно
cd "$(dirname "$0")/app" || exit 1

if [ ! -f "gui.py" ]; then
    echo "Не найден app/gui.py"
    exit 1
fi

python3 -m py_compile gui.py || exit 1
python3 gui.py
