PYTHON ?= python3.7
REQUIREMENTSTXT ?= requirements_3.7.txt

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    venv           Create virtual-environment for the project"
	@echo "    requirements   Install requirements of the project"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    PYTHON         Default '$(PYTHON)'."
	@echo "    REQS           Default '$(REQUIREMENTSTXT)'."


venv:
	$(PYTHON) -m venv venv
	venv/bin/pip install -r $(REQUIREMENTSTXT)

start-mongo: .env
	docker-compose up -d mongo

.env:
	cp things/env-template .env
