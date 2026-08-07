.PHONY: install run-honeypot run-dashboard seed test lint docker-up

install:
	pip install -r requirements.txt

run-honeypot:
	python -m honeypot.server

run-dashboard:
	python -m dashboard.app

seed:
	python tools/seed.py --count 60

test:
	pytest -v

lint:
	ruff check .

docker-up:
	docker compose up --build