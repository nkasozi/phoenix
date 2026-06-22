default_path = projects/hugging_face_classifier

run_bash_in_container:
	@echo "Starting up the development environment..."
	docker compose run --rm hugging_face bash

NVIDIA_COMPOSE_COMMAND=docker compose -f compose.yaml -f compose.nvidia.yaml

nvidia_run:
	@echo "Starting up the nvidia development environment..."
	$(NVIDIA_COMPOSE_COMMAND) run --rm hugging_face_nvidia bash

nvidia_build:
	@echo "Building the nvidia development environment..."
	$(NVIDIA_COMPOSE_COMMAND) build

build:
	@echo "Building the development and CI environment..."
	docker compose build

all:
	@echo "Running `all` in ci environment"
	@echo "Starting lint based on parent configuration"
	docker compose run --rm hugging_face make lint path=$(default_path)
	@echo "Starting type check based on hugging_face_classifier configuration"
	docker compose run \
		--rm \
		-w /app/projects/hugging_face_classifier/ \
		hugging_face mypy .
	@echo "Starting test based on parent configuration"
	docker compose run --rm hugging_face make test path=$(default_path)

format:
	@echo "Running `format` in ci environment"
	docker compose run --rm hugging_face make format path=$(default_path)

clean:
	@echo "Cleaning the development environment..."
	docker compose down -v --remove-orphans

test:
	@echo "Running `format` in ci environment"
	@echo "Running tests for path $(path) with args $(PYTEST_ARGS_OVERRIDE)"
	docker compose run --rm -e PYTEST_ARGS_OVERRIDE="$(PYTEST_ARGS_OVERRIDE)" hugging_face make test path=$(default_path)

test_integration:
	@echo "Running `tests/integration` in dev environment"
	@echo "Currently dev environment is the only environment with gcloud credentials setup."
	docker compose run --rm -e PYTEST_ARGS_OVERRIDE="tests/integration/" hugging_face make test path=$(default_path)

prefect_deploy_all:
	@echo "Deploying all flows to Prefect Cloud"
	@echo "Using environment variables"
	@echo "Work pool: $(HF_WORK_POOL)"
	@echo "Image: $(HF_IMAGE)"
	docker compose run --rm hugging_face prefect deploy --all --prefect-file projects/hugging_face_classifier/prefect.yaml

nvidia_test_integration:
	@echo "Running `tests/integration` in nvidia dev environment"
	@echo "Currently dev environment is the only environment with gcloud credentials setup."
	$(NVIDIA_COMPOSE_COMMAND) run --rm -e PYTEST_ARGS_OVERRIDE="tests/integration/" hugging_face_nvidia make test path=$(default_path)

nvidia_all:
	@echo "Running `all` in nvidia ci environment"
	@echo "Starting lint based on parent configuration"
	$(NVIDIA_COMPOSE_COMMAND) run --rm hugging_face_nvidia make lint path=$(default_path)
	@echo "Starting type check based on hugging_face_classifier configuration"
	$(NVIDIA_COMPOSE_COMMAND) run \
		--rm \
		-w /app/projects/hugging_face_classifier/ \
		hugging_face_nvidia mypy .
	@echo "Starting test based on parent configuration"
	$(NVIDIA_COMPOSE_COMMAND) run --rm hugging_face_nvidia make test path=$(default_path)
