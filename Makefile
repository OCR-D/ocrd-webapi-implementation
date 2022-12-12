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
	@echo "    test-api       Run only API tests (faster)"
	@echo "    test-rabbitmq  Run only RabbitMQ tests (faster)"
	@echo ""
	@echo "  Variables"
	@echo "    PYTHON         Default '$(PYTHON)'."
	@echo "    REQS           Default '$(REQUIREMENTSTXT)'."

venv:
	$(PYTHON) -m venv webapi-venv
	webapi-venv/bin/pip install -r $(REQUIREMENTSTXT)

start: start-mongo start-rabbitmq start-server

start-mongo:
	docker-compose --env-file things/env-template-localdev up -d mongo

start-rabbitmq:
	docker-compose --env-file things/env-template-localdev up -d webapi-rabbit-mq

start-server:
	uvicorn ocrd_webapi.main:app --host 0.0.0.0 --reload

test: test-api test-rabbitmq test-utils

test-api:
	OCRD_WEBAPI_STORAGE_DIR='/tmp/ocrd_webapi_test' \
	OCRD_WEBAPI_DB_URL='mongodb://localhost:6701/test-ocrd-webapi' \
	OCRD_WEBAPI_USERNAME='test' \
	OCRD_WEBAPI_PASSWORD='test' \
	pytest tests/*_api.py

test-rabbitmq:
	pytest tests/*rabbit*.py

test-utils:
	pytest tests/*utils*.py
