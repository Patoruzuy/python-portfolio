# Makefile for Python Portfolio
.PHONY: help install dev prod test clean docker-build docker-up docker-down docker-logs migrate seed backup

# Default target
help:
	@echo "Python Portfolio - Available Commands:"
	@echo ""
	@echo "  make install       - Install dependencies"
	@echo "  make dev           - Run development server (Flask + Celery)"
	@echo "  make test          - Run tests with coverage"
	@echo "  make clean         - Clean up cache files"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start all services (Flask + Celery + Redis)"
	@echo "  make docker-down   - Stop all services"
	@echo "  make docker-logs   - View logs"
	@echo "  make docker-shell  - Open shell in web container"
	@echo ""
	@echo "Database Commands:"
	@echo "  make migrate       - Run database migrations"
	@echo "  make seed          - Seed database with sample data"
	@echo "  make backup        - Backup database"
	@echo "  make create-admin  - Create admin user"
	@echo ""

# Install dependencies
install:
	pip install -r requirements.txt

# Run development servers (Flask + Celery)
dev:
	@echo "Starting Redis (make sure Redis is running)..."
	@echo "Starting Celery worker in background..."
	start /B celery -A celery_config.celery worker --loglevel=info --pool=solo
	@echo "Starting Flask development server..."
	python app.py

# Run tests
test:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

# Clean cache and temporary files
clean:
	@echo "Cleaning cache files..."
	del /S /Q *.pyc 2>nul
	rmdir /S /Q __pycache__ 2>nul
	rmdir /S /Q .pytest_cache 2>nul
	rmdir /S /Q htmlcov 2>nul
	rmdir /S /Q .coverage 2>nul
	@echo "Clean complete!"

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "Services started! Access at http://localhost:5000"
	@echo "View logs with: make docker-logs"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-shell:
	docker-compose exec web /bin/bash

# Database commands
migrate:
	python scripts/migrate_to_new_schema.py

seed:
	python -c "from scripts.migrate_to_new_schema import seed_sample_data; seed_sample_data()"

backup:
	@echo "Creating database backup..."
	if not exist backups mkdir backups
	copy portfolio.db backups\portfolio_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.db
	@echo "Backup complete!"

create-admin:
	python -c "from models import db, User; from app import app; \
	with app.app_context(): \
		username = input('Username: '); \
		email = input('Email: '); \
		password = input('Password: '); \
		user = User(username=username, email=email, is_superuser=True); \
		user.set_password(password); \
		db.session.add(user); \
		db.session.commit(); \
		print(f'Admin user {username} created!')"

# Production deployment
prod:
	@echo "Starting production server with Waitress..."
	waitress-serve --host=0.0.0.0 --port=5000 --threads=4 app:app
