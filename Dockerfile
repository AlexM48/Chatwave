# Dockerfile
# Базовый образ Python
FROM python:3.12-slim-bullseye

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

# Копируем зависимости заранее (для кэширования)
COPY requirements.txt /app/requirements.txt

# Устанавливаем зависимости
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Копируем проект в контейнер
COPY . /app

# Создаём папку logs и файлы логов, чтобы Django не падал
RUN mkdir -p /app/logs \
    && touch /app/logs/error.log /app/logs/info.log \
    && chown -R appuser:appuser /app/logs

# Создаём пользователя для запуска приложения
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Экспонируем порт Daphne
EXPOSE 8000

# Копируем и делаем исполняемым entrypoint
COPY ./docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh

# По умолчанию запускаем entrypoint
ENTRYPOINT ["/app/docker/entrypoint.sh"]

# Запускаем Daphne внутри entrypoint
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "chatwave.asgi:application"]
