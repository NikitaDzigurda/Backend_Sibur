FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install --no-cache-dir poetry

# Установка рабочей директории
WORKDIR /app

# Копирование файлов Poetry
COPY pyproject.toml poetry.lock* ./

# Установка зависимостей проекта
RUN poetry config virtualenvs.create false && poetry install

# Копирование всего кода проекта
COPY . .

# Команда по умолчанию: ожидание базы, миграции и запуск приложения
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]