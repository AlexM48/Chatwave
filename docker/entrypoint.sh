#!/usr/bin/env bash
set -e

# Скрипт запуска контейнера:
# - ждём доступности БД (если нужно)
# - применяем миграции
# - собираем статику (collectstatic)
# - запускаем CMD (daphne) переданную из Dockerfile

# Загружаем .env в окружение, если файл есть (опционально)
if [ -f /app/.env ]; then
  export $(grep -v '^#' /app/.env | xargs)
fi

# Ожидаем БД (Postgres) — по переменной DATABASE_HOST
if [ -n "$DATABASE_HOST" ]; then
  echo "Waiting for database at $DATABASE_HOST:$DATABASE_PORT..."
  # netcat — ждём открытия порта
  /usr/bin/env bash -c 'until nc -z "$DATABASE_HOST" "$DATABASE_PORT"; do echo "Waiting for postgres..."; sleep 1; done'
fi

# Выполняем миграции
echo "Apply migrations"
python manage.py migrate --noinput

# Собираем статику (для production)
echo "Collect static files"
python manage.py collectstatic --noinput

# Можно создавать суперпользователя или применять иниты (опционально)
# python manage.py loaddata initial_data.json || true

# Наконец исполняем команду контейнера (CMD)
echo "Starting server: $@"
exec "$@"
