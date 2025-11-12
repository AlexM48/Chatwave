# ChatWave — Реалтайм чат на Django + Channels + WebSockets

**ChatWave** — это веб-приложение для обмена сообщениями в реальном времени.  
Создано на **Django**, **Channels**, **Redis** и развёртывается через **Docker Compose** с **Nginx** в качестве обратного прокси.

---

## Основные технологии

- **Backend:** Django 5 + Django Channels (ASGI)
- **WebSockets:** реализация чатов в реальном времени
- **Брокер:** Redis (для обмена сообщениями между consumers)
- **Frontend:** HTML + TailwindCSS + JS (без фреймворков)
- **База данных:** PostgreSQL
- **Инфраструктура:** Docker + Docker Compose
- **Reverse Proxy:** Nginx
- **Production ready:** статические файлы, миграции, entrypoint, `.env`

---

## Структура проекта

