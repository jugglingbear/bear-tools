# Type "make help" to get colorful help text for each target
.PHONY: help
help:
	@echo "\n\033[1mAvailable targets:\033[0m"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: build-docs
build-docs:  ## Build the static MkDocs site
	@echo '👷🏻 Building the docs website'
	poetry run mkdocs build

.PHONY: coverage
coverage: src/bear_tools
	@echo '🎯 Analyzing unit test code coverage'
	poetry run pytest --cov=src/bear_tools --cov-report=term-missing

.PHONY: clean
clean:  ## Remove generated site files and intermediate build artifacts
	@echo '🧼 Tidying up'
	rm -rf site

.PHONY: docs-dev
docs-dev: clean build-docs serve-docs  ## Build and serve the docs website locally as http://localhost:8000

.PHONY: lint
lint: src/bear_tools
	@echo '🧹 Running flake8'
	poetry run flake8 src/bear_tools
	@echo '🔍 Running mypy'
	poetry run mypy src/bear_tools

.PHONY: serve-docs
serve-docs:  ## Launch the live-reloading local MkDocs development server
	@echo '🌐 Running local docs server'
	poetry run mkdocs serve
