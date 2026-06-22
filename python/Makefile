all: check_path_exists lint typecheck test

check_path_exists:
	@if [ -z "$(path)" ]; then \
		echo "Path argument is required; add \`path=...\` to the make command."; \
		exit 1; \
	fi

format: check_path_exists
	@echo "Running format for path $(path)..."
	cd $(path) && ruff format .
	cd $(path) && ruff check --fix .

lint: check_path_exists
	@echo "Running lint for path $(path)..."
	cd $(path) && ruff format --check .
	cd $(path) && ruff check .

typecheck: check_path_exists
	@echo "Running typecheck for path $(path)..."
	@if echo "$(path)" | grep -qE '^libs/'; then \
		echo "Path is a library, running mypy only on library"; \
		mypy_cmd="mypy $(path)"; \
	elif echo "$(path)" | grep -qE '^projects/'; then \
		local_libs=$$(grep -E '^-e file:libs/' $(path)/requirements.txt | sed 's|^-e file:libs/|libs/|' | tr '\n' ' '); \
		if [ -n "$$local_libs" ]; then \
			echo "Found local libs for project, running mypy on project and libs: $$local_libs"; \
			mypy_cmd="mypy $(path) $$local_libs"; \
		else \
			echo "No local libs found for project, running mypy only on project"; \
			mypy_cmd="mypy $(path)"; \
		fi; \
	fi; \
	mypy_cmd="$${mypy_cmd}"; \
	echo "Running mypy command: $$mypy_cmd"; \
	eval $$mypy_cmd

# Test command assumes directory structure where test directory is nested within the python package
# E.g. `projects/example_project_1/example_project_1/tests` is the directory location and the
# corresponding make command is `make test path=projects/example_project_1/` so that usage is
# consistent with other make commands.
test: check_path_exists
	@echo "Running tests for path $(path)..."
	@echo "Test args: $${PYTEST_ARGS_OVERRIDE:-tests}"
	@normalized_path=$$(echo "$(path)" | sed 's:/*$$::'); \
	base_dir=$$(basename $$normalized_path); \
	cd $$normalized_path/$$base_dir && eval pytest $${PYTEST_ARGS_OVERRIDE:-tests}

check_path_is_project:
	@if echo "$(path)" | grep -qvE '^projects/'; then \
		echo "This make command should only be ran for projects, not libraries."; \
		exit 1; \
	fi

compile_requirements: check_path_exists check_path_is_project
	@echo "Running compile for path $(path)..."
	pip-compile $(path)/requirements.in

upgrade_requirements: check_path_exists check_path_is_project
	@echo "Running upgrade for path $(path)..."
	pip-compile --upgrade $(path)/requirements.in

create_venv: check_path_exists
	# Normalise the path by removing any trailing slashes
	@normalized_path=$$(echo "$(path)" | sed 's:/*$$::'); \
	venv_name=".$$(basename $$normalized_path)_venv"; \
	echo "Creating venv for path $$normalized_path at $$venv_name..."; \
	python -m venv $$normalized_path/$$venv_name; \
	echo "Run 'source $$normalized_path/$$venv_name/bin/activate' to activate the venv."

install: check_path_exists
	@echo "Installing for path $(path)..."
	@if echo "$(path)" | grep -qE '^projects/'; then \
		pip install -r $(path)/requirements.txt; \
	elif echo "$(path)" | grep -qE '^libs/'; then \
		pip install -r dev-requirements.txt; \
	fi
	pip install -e $(path)/.
	pre-commit install
