#FROM python:3.11-slim
#
## Установка системных зависимостей
#RUN apt-get update && apt-get install -y \
#    gcc \
#    postgresql-client \
#    && rm -rf /var/lib/apt/lists/*
#
## Установка Poetry
#RUN pip install --no-cache-dir poetry
#
## Установка рабочей директории
#WORKDIR /app
#
## Копирование файлов Poetry
#COPY pyproject.toml poetry.lock* ./
#
## Установка зависимостей проекта
#RUN poetry config virtualenvs.create false && poetry install
#
## Копирование всего кода проекта
#COPY . .
#
## Команда по умолчанию: ожидание базы, миграции и запуск приложения
#CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

# Стадия 1: Сборка фронтенда (предположительно React)
FROM node:18 AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Стадия 2: Сборка бэкенда
FROM python:3.11-slim AS backend-build
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry
WORKDIR /app/backend
COPY backend/pyproject.toml backend/poetry.lock* ./
RUN poetry config virtualenvs.create false && poetry install --no-dev
COPY backend/ ./

# Стадия 3: Финальный образ с Nginx и бэкендом
FROM nginx:alpine
# Копируем статические файлы фронтенда
COPY --from=frontend-build /app/frontend/build /usr/share/nginx/html
# Копируем бэкенд
COPY --from=backend-build /app/backend /app/backend
# Копируем конфигурацию Nginx
COPY nginx.conf /etc/nginx/nginx.conf
# Устанавливаем Python и Uvicorn
RUN apk add --no-cache python3 py3-pip \
    && pip install --no-cache-dir uvicorn
# Устанавливаем рабочую директорию
WORKDIR /app/backend
# Открываем порт для Nginx
EXPOSE 80
# Запускаем миграции, Uvicorn и Nginx
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 & nginx -g 'daemon off;'"]