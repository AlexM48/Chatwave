# Dockerfile
# Базовый образ Python. Можно поменять на python:3.12-slim-bullseye (в зависимости от ОС).
FROM python:3.12-slim

# Метаданные
LABEL maintainer="you@example.com"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Установим системные зависимости, необходимые для Pillow, ffmpeg (опционально), build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    netcat-openbsd \
    gettext \
    ffmpeg \            
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория приложения
WORKDIR /app

# Копируем зависимости заранее (для использования docker cache)
COPY requirements.txt /app/requirements.txt

# Установим pip зависимости
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# Копируем проект в контейнер
COPY . /app

# Создаём пользователя для запуска приложения (security)
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Экспонируем порт Daphne (в контейнере)
EXPOSE 8000

# Копируем и делаем исполняемым entrypoint
COPY ./docker/entrypoint.sh /app/docker/entrypoint.sh
#RUN chmod +x /app/docker/entrypoint.sh

# По-умолчанию запускаем entrypoint (migrations, collectstatic, запуск сервера)
ENTRYPOINT ["/app/docker/entrypoint.sh"]
# Запускаем daphne внутри entrypoint
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "chatwave.asgi:application"]
