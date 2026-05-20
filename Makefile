ALEMBIC=alembic
ENV_COMPOSE_FILE = -f "docker-compose.local.yml"

.PHONY: makemigrations
makemigrations:
	@read -p "Enter name migrations: " message; \
	$(ALEMBIC) revision --autogenerate -m "$$message"

.PHONY: migrate
migrate:
	@$(ALEMBIC) upgrade head

.PHONY: downgrade
downgrade:
	@$(ALEMBIC) downgrade -1

.PHONY: current
current:
	@$(ALEMBIC) current

.PHONY: history
history:
	@$(ALEMBIC) history

.PHONY: up_local_environment
up_local_environment:
	docker compose $(ENV_COMPOSE_FILE) -p zone3000_local up --build


.PHONY: run_app
run_api:
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4


.PHONY: run_retry
run_retry:
	PYTHONPATH=. python -m workers.retry.main


.PHONY: run_classify
run_classify:
	PYTHONPATH=. python -m workers.classify.main