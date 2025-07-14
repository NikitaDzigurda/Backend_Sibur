.PHONY: dev install format lint

# Запуск FastAPI сервера с перезагрузкой
dev:
	poetry run uvicorn app.main:app --reload

install-library:
	@echo "Installing dependency $(LIBRARY)"
	poetry add $(LIBRARY)

migrate-create:
	alembic revision --autogenerate -m $(MIGRATION)

migrate-apply:
	alembic upgrade head

install:
	poetry install