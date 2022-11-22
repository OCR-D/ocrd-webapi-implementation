PYTHON ?= python3.7
REQUIREMENTSTXT ?= requirements.txt

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    venv           Create virtual-environment for the project"
	@echo "    start-mongo    start mongodb for local dev environment"
	@echo "    test           Run all available tests"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    PYTHON         Default '$(PYTHON)'."
	@echo "    REQS           Default '$(REQUIREMENTSTXT)'."


venv:
	$(PYTHON) -m venv webapi-venv
	webapi-venv/bin/pip install -r $(REQUIREMENTSTXT)

start-mongo:
	docker-compose --env-file things/env-template-localdev up -d mongo

test:
	pytest tests
