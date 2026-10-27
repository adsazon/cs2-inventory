# CS2 Inventory Value

Мини-сервис для учёта инвентаря CS2: добавление/удаление предметов (полное и частичное), просмотр, расчёт суммы и суммы с комиссией.

## Установка

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements-dev.txt

## Запуск (без --reload)

    python -m uvicorn app_final:app --host 0.0.0.0 --port 8000

Документация: http://127.0.0.1:8000/docs

## Переменные окружения

- APP_NAME — название сервиса (default: CS2 Inventory Value)
- DEFAULT_COMMISSION_PCT — комиссия по умолчанию (default: 15)
- MAX_ITEMS — лимит позиций (default: 50)

## Тесты

    python -m pytest -v

## Проверка и диагностика

    curl http://127.0.0.1:8000/health
    curl http://127.0.0.1:8000/version
    curl -X POST http://127.0.0.1:8000/inventory/ak47 \
      -H "Content-Type: application/json" -d '{"price":35.0,"qty":5}'
    curl http://127.0.0.1:8000/inventory
    curl http://127.0.0.1:8000/inventory/ak47
    curl http://127.0.0.1:8000/inventory/total
    curl "http://127.0.0.1:8000/inventory/total?commission=10"
    curl -X DELETE http://127.0.0.1:8000/inventory/ak47/2
    curl -X DELETE http://127.0.0.1:8000/inventory/ak47

## Обработка ошибок

- 400 — удаление больше, чем есть / превышен MAX_ITEMS
- 404 — предмет не найден
- 422 — невалидные входные данные
- 500 — непредвиденная ошибка (лог с трейсбеком)

Логи: stdout uvicorn (INFO).