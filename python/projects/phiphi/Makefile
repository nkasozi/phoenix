
default_path = projects/phiphi/
phiphi_gitlab_repo = registry.gitlab.com/howtobuildup/phoenix/python/phiphi
tag ?= latest
image ?= "$(phiphi_gitlab_repo):$(tag)"
override_work_pool_name ?= local-work-pool
group_name ?= local
project_db_alembic_ini ?= project_db.alembic.ini

DEV_COMPOSE_COMMAND=docker compose -f compose.yaml -f compose.dev.yaml

up:
	@echo "Starting up the development environment..."
	@docker network create phoenix_shared 2>/dev/null || true
	$(DEV_COMPOSE_COMMAND) up

down:
	@echo "Shutting down the development environment..."
	$(DEV_COMPOSE_COMMAND) down

run_bash_in_container:
	@echo "Starting a bash session in the api container..."
	@echo "You can run any command in the api container, "
	@echo "Run api server to interatce with pdb.set_trace: "
	@echo "uvicorn phiphi.api.main:app --reload --host 0.0.0.0 --port 80 --log-config /app/projects/phiphi/log_configs/uvicorn.dev.yaml"
	$(DEV_COMPOSE_COMMAND) run --service-ports --rm api bash

build:
	@echo "Building the development and CI environment..."
	docker compose build

clean:
	@echo "Clean the development environment..."
	docker compose down -v --remove-orphans
	@echo "Clean the projects db for migrations..."
	rm -rf local_project_dbs/alembic.db

bash_in_api:
	@echo "Starting bash in the dev api environment"
	$(DEV_COMPOSE_COMMAND) exec api bash

all: check_alembic_heads
	@echo "Running `all` in ci environment"
	docker compose run --rm api make all path=$(default_path)

test:
	@echo "Running `format` in ci environment"
	@echo "Running tests for path $(path) with args $(PYTEST_ARGS_OVERRIDE)"
	docker compose run --rm -e PYTEST_ARGS_OVERRIDE="$(PYTEST_ARGS_OVERRIDE)" api make test path=$(default_path)

INTEGRATION_DOCKER_COMPOSE_COMMAND=docker compose -f compose.yaml -f compose.dev.yaml -f compose.integration.yaml

up_integration:
	@echo "Starting up the integration environment..."
	@echo "Currently dev environment is the only environment with gcloud credentials setup."
	$(INTEGRATION_DOCKER_COMPOSE_COMMAND) up

test_integration:
	@echo "Running tests/integration in dev environment"
	@if [ -z "$(PYTEST_ARGS_OVERRIDE)" ]; then \
	  export PYTEST_ARGS_OVERRIDE="tests/integration/"; \
	fi; \
	echo "Running tests with args $$PYTEST_ARGS_OVERRIDE"; \
	$(INTEGRATION_DOCKER_COMPOSE_COMMAND) run --rm \
		-e PYTEST_ARGS_OVERRIDE="$$PYTEST_ARGS_OVERRIDE" \
		api make test path=$(default_path)

clean_bq_test_datasets:
	@if [ -z "$(GCP_PROJECT_ID)" ]; then \
	  echo "Error: GCP_PROJECT_ID is required."; \
	  echo "Usage: make clean_bq_test_datasets GCP_PROJECT_ID=your-gcp-project-id"; \
	  exit 1; \
	fi
	@echo "Cleaning up BigQuery test datasets in project $(GCP_PROJECT_ID)"
	@./clean_bq_test_datasets.sh $(GCP_PROJECT_ID)

format:
	@echo "Running `format` in ci environment"
	docker compose run --rm api make format path=$(default_path)

push_phiphi_image:
	@echo "Pushing the phiphi image to the registry for tag $(tag)"
	@if [ "$(tag)" = "main" ] || [ "$(tag)" = "dev" ]; then \
			echo "Error: Pushing to 'main' or 'dev' tags is not allowed!"; \
			exit 1; \
	else \
			docker tag phiphi:latest $(phiphi_gitlab_repo):$(tag); \
			docker push $(phiphi_gitlab_repo):$(tag); \
	fi

# Usage: make prefect_init image=registry.gitlab.com/howtobuildup/phoenix/python/phiphi:main
# This function can be used in k8 job or a CI to initialize the Prefect cloud/server workspace. See
# the prefect_init.py for more information.
prefect_init:
	@echo "Initialize prefect project"
	$(DEV_COMPOSE_COMMAND) run --rm api python projects/phiphi/phiphi/prefect_init.py --image $(image)

# Usage: make create_prefect_deployments image=registry.gitlab.com/howtobuildup/phoenix/python/phiphi:main
# This function can be used in CI to create all prefect deployments with the image that it has
# just published
create_prefect_deployments:
	@echo "Create prefect deployments"
	$(DEV_COMPOSE_COMMAND) run --rm api python projects/phiphi/phiphi/prefect_deployments.py --image $(image)

create_prefect_grouped_deployments:
	@echo "Building and pushing phiphi image with tag $(group_name)"
	make build
	tag=$(group_name) make push_phiphi_image
	@echo "Create grouped deployments for development and testing"
	$(DEV_COMPOSE_COMMAND) run --rm api python projects/phiphi/phiphi/prefect_grouped_deployments.py \
			--override_work_pool_name $(override_work_pool_name) \
			--group_name $(group_name)

fix_local_permissions:
	sudo chown -R $(USER):$(USER) phiphi/

# We are using an extra docker compose file to run alembic commands
# because there are a few differences in the environment setup
# when running an alembic command.
ALEMBIC_DOCKER_COMPOSE_COMMAND=docker compose -f compose.yaml -f compose.alembic.yaml run --rm api

check_alembic_heads:
	@echo "Checking for multiple Alembic heads..."
	$(ALEMBIC_DOCKER_COMPOSE_COMMAND) python check_alembic_heads.py

alembic_revision:
	@if [ -z "$(message)" ]; then \
		echo "message argument is required; add \`message=...\` to the make command."; \
		exit 1; \
	fi
	echo "WARNING: something is wrong with the processing the command and so you can't have spaces in the message."
	$(ALEMBIC_DOCKER_COMPOSE_COMMAND) alembic revision --autogenerate -m "$(message)"

UPGRADE_REVISION ?= heads
# Usage: make alembic_upgrade UPGRADE_REVISION=base
# Default is head
alembic_upgrade:
	$(ALEMBIC_DOCKER_COMPOSE_COMMAND) alembic upgrade $(UPGRADE_REVISION)

DOWNGRADE_REVISION ?= -1
# Usage: make alembic_downgrade DOWNGRADE_REVISION=base
# or
# make alembic_downgrade DOWNGRADE_REVISION=-1
# Default is -1
alembic_downgrade:
	$(ALEMBIC_DOCKER_COMPOSE_COMMAND) alembic downgrade $(DOWNGRADE_REVISION)

# Project alembic
project_alembic_revision:
	@if [ -z "$(message)" ]; then \
		echo "message argument is required; add \`message=...\` to the make command."; \
		exit 1; \
	fi
	echo "WARNING: something is wrong with the processing the command and so you can't have spaces in the message."
	$(ALEMBIC_DOCKER_COMPOSE_COMMAND) alembic -c $(project_db_alembic_ini) revision --autogenerate -m "$(message)"

# Usage: make project_alembic_upgrade UPGRADE_REVISION=base
# Default is head
project_alembic_upgrade:
	@echo "Upgrading the project database"
	@echo "UPGRADE_REVISION=$(UPGRADE_REVISION)"
	@echo "The migrations will be applied to an SQLite database which is only used for development of migrations."
	@echo "See sqlalchemy.url in the project_db.alembic.ini for more information."
	$(ALEMBIC_DOCKER_COMPOSE_COMMAND) alembic -c $(project_db_alembic_ini) upgrade $(UPGRADE_REVISION)

DOWNGRADE_REVISION ?= -1
# Usage: make project_alembic_downgrade DOWNGRADE_REVISION=base
# or
# make alembic_downgrade DOWNGRADE_REVISION=-1
# Default is -1
project_alembic_downgrade:
	$(ALEMBIC_DOCKER_COMPOSE_COMMAND) alembic -c $(project_db_alembic_ini) downgrade $(DOWNGRADE_REVISION)


psql_dev:
	@echo "Connecting to the development database..."
	@echo "default password is 'password'"
	psql -h localhost -p 5432 -U postgres -d dev_db

psql_test:
	@echo "Connecting to the test database..."
	@echo "default password is 'password'"
	psql -h localhost -p 5433 -U postgres -d test_db

reseed_testing:
	@echo "Reseeding the database with test data"
	docker compose run --rm api python projects/phiphi/phiphi/seed/main.py --testing

