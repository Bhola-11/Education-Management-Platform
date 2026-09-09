# EduTrack Enterprise Platform Makefile
.PHONY: install migrate run test verify clean

install:
	pip install -r requirements.txt

migrate:
	python manage.py makemigrations
	python manage.py migrate

run:
	python main.py

test:
	pytest tests/

verify:
	python manage.py check --deploy

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
