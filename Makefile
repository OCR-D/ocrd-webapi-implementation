PYTHON ?= python3.7
REQUIREMENTSTXT ?= requirements.txt

help:
	@echo ""
	@echo "  Targets"
	@echo "    venv           Create virtual-environment for the project"
	@echo "    start          Start MongoDB Docker + WebAPI Server"
	@echo "    start-mongo    Start MongoDB Docker container"
	@echo "    start-rabbitmq Start RabbitMQ Docker container"
	@echo "    start-server   Start the WebAPI Server"
	@echo "    test           Run all available tests"
	@echo "    test-api       Run only api tests (faster)"
	@echo ""
	@echo "  Variables"
	@echo "    PYTHON         Default '$(PYTHON)'."
	@echo "    REQS           Default '$(REQUIREMENTSTXT)'."


venv:
	$(PYTHON) -m venv webapi-venv
	webapi-venv/bin/pip install -r $(REQUIREMENTSTXT)

start:
	docker-compose --env-file things/env-template-localdev up -d mongo
		uvicorn ocrd_webapi.main:app --host 0.0.0.0 --reload

start-mongo:
		docker-compose --env-file things/env-template-localdev up -d mongo

start-rabbitmq:
		docker-compose --env-file things/env-template-localdev up -d webapi-rabbit-mq

start-server:
		uvicorn ocrd_webapi.main:app --host 0.0.0.0 --reload

test:
	pytest tests

test-api:
	pytest tests/*_api.py
