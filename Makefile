VIRTUAL_ENV ?= $(CURDIR)/venv
PYTHON ?= python3.7

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


venv:
	$(PYTHON) -m venv venv

requirements:
	pip install -r requirements.txt