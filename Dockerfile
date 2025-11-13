# Dockerfile
# Базовый образ Python
FROM python:3.12-slim-bullseye

# Метаданные
LABEL maintainer="you@example.com"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Установим системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    netcat-openbsd \
    gettext \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Создаём пользователя до копирования проекта
RUN useradd --create-home --shell /bin/bash appuser

# Рабочая директория приложения
WORKDIR /app

# Копируем зависимости заранее (для кэширования)
COPY requirements.txt /app/requirements.txt

# Устанавливаем зависимости
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Копируем проект в контейнер
COPY . /app

# Создаём папку logs и файлы логов, чтобы Django не падал, и меняем владельца на appuser
RUN mkdir -p /app/logs \
    && touch /app/logs/error.log /app/logs/info.log \
    && chmod +x /app/docker/entrypoint.sh \
    && chown -R appuser:appuser /app

# Переключаемся на пользователя
USER appuser

# Экспонируем порт Daphne
EXPOSE 8000

# По умолчанию запускаем entrypoint
ENTRYPOINT ["/app/docker/entrypoint.sh"]

# Запускаем Daphne внутри entrypoint
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "chatwave.asgi:application"]
