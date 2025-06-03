# Type "make help" to get colorful help text for each target
.PHONY: help
help:
	@echo "\n\033[1mAvailable targets:\033[0m"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: coverage
coverage: src/bear_tools  ## Analyze test code coverage
	@echo '🎯 Analyzing test code coverage'
	poetry run pytest --cov=src/bear_tools --cov-report=term-missing --cov-context=test

.PHONY: clean
clean:  ## Remove generated site files and intermediate build artifacts
	@echo '🧼 Tidying up'
	rm -rf site

.PHONY: docs-dev
docs-dev: clean ## Build and serve the docs website locally as http://localhost:8000
	@echo '👷🏻 Building the docs website'
	poetry run mkdocs build
	@echo '🌐 Running local docs server'
	poetry run mkdocs serve

.PHONY: lint  
lint: src/bear_tools  ## Run flake8 and mypy on the src/bear_tools package
	@echo '🧹 Running flake8'
	poetry run flake8 src/bear_tools
	@echo '🔍 Running mypy'
	poetry run mypy src/bear_tools

.PHONY: publish
publish: src/bear_tools  ## Publish changes to PyPi
	@echo '📦 Building release package for PyPi'
	poetry build
	poetry publish

.PHONY: test
test: src/bear_tools  ## Run unit tests
	@echo '🧪 Run unit tests'
	poetry run pytest tests
