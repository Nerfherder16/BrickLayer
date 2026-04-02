.PHONY: lint test build

lint:
	cd backend && ruff check .

test:
	pytest tests/

build:
	docker compose build
