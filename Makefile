.DEFAULT_GOAL := help

help: ## Shows this help message
	@printf "\033[1m%s\033[36m %s\033[32m %s\033[0m \n\n" "Development environment for" "aioskybell" "";
	@awk 'BEGIN {FS = ":.*##";} /^[a-zA-Z_-]+:.*?##/ { printf " \033[36m make %-25s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST);
	@echo

requirements: ## Install requirements
	@python3 -m pip --disable-pip-version-check install -r requirements.txt

lint: ## Lint all files
	@isort .
	@python3 -m black --fast .
	@python3 -m pylint aioskybell tests
	@python3 -m flake8 aioskybell tests
	@python3 -m mypy aioskybell

coverage: ## Check the coverage of the package
	@python3 -m pytest tests --asyncio-mode=strict --cov=aioskybell --cov-report term-missing -vv

setup: ## Setup the package
	@python3 setup.py develop