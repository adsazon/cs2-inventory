# CS2 Inventory Value

Мини-сервис для учёта инвентаря CS2: добавление предметов, просмотр и расчёт стоимости с комиссией.

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

## Проверка

    curl http://127.0.0.1:8000/health
    curl http://127.0.0.1:8000/inventory/total