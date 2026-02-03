.PHONY: help build up down restart logs shell migrate createsuperuser collectstatic test lint setwebhook deletewebhook webhookinfo

help:
	@echo "Available targets:"
	@echo "  build          - docker-compose build"
	@echo "  up             - docker-compose up -d"
	@echo "  down           - docker-compose down"
	@echo "  restart        - restart django container"
	@echo "  logs           - follow logs"
	@echo "  shell          - open django shell"
	@echo "  migrate        - run migrations"
	@echo "  createsuperuser- create admin user"
	@echo "  collectstatic  - collect static files"
	@echo "  test           - run Django tests"
	@echo "  lint           - basic flake8 lint (if installed)"
	@echo "  setwebhook     - set Telegram webhook"
	@echo "  deletewebhook  - delete Telegram webhook"
	@echo "  webhookinfo    - get current webhook info"
	@echo "  celery         - run celery worker (docker compose)"
	@echo "  celery-beat    - run celery beat (docker compose)"
	@echo "  celery-logs    - follow celery worker logs"
	@echo "  beat-logs      - follow celery beat logs"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart mendeleyev_django

logs:
	docker compose logs -f --tail=200

shell:
	docker compose exec mendeleyev_django python manage.py shell

migrate:
	docker compose exec mendeleyev_django python manage.py migrate

createsuperuser:
	docker compose exec mendeleyev_django python manage.py createsuperuser

collectstatic:
	docker compose exec mendeleyev_django python manage.py collectstatic --noinput

test:
	# Explicit test labels to avoid discovery import ambiguity
	docker compose exec mendeleyev_django python manage.py test auth.users.tests auth.profiles.tests apps.branch.tests.test_membership apps.branch.tests.test_managed_branches apps.botapp.tests -v 2

lint:
	- docker compose exec mendeleyev_django flake8 || true

setwebhook:
	docker compose exec mendeleyev_django python manage.py setwebhook --drop-pending

deletewebhook:
	docker compose exec mendeleyev_django python manage.py deletewebhook

webhookinfo:
	docker compose exec mendeleyev_django python manage.py webhookinfo

celery:
	docker compose up -d mendeleyev_celery

celery-beat:
	docker compose up -d mendeleyev_celery_beat

celery-logs:
	docker compose logs -f mendeleyev_celery

beat-logs:
	docker compose logs -f mendeleyev_celery_beat
