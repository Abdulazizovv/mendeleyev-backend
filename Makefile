run:
	python manage.py runserver 0.0.0.0:8000

migrate:
	python manage.py migrate

setwebhook:
	python manage.py setwebhook --drop-pending

deletewebhook:
	python manage.py deletewebhook

test:
	python manage.py test -v 2
