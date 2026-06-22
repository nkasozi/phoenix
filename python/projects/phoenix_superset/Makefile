build:
	docker compose build

up:
	@echo "Starting the development environment..."
	@echo "A rebuild is always done as there is no mount"
	docker compose up --build

bash_superset:
	@echo "Starting a bash session in the superset container..."
	docker compose exec -u root phoenix_superset bash

clean:
	@echo "Clean the development environment..."
	docker compose down -v --remove-orphans

init:
	@echo "Initializing the development environment..."
	docker compose exec phoenix_superset superset fab create-admin \
              --username admin \
              --firstname Admin \
              --lastname Admin \
              --email admin@admin.com \
              --password admin
	docker compose exec phoenix_superset superset db upgrade
	docker compose exec phoenix_superset superset init
	@echo ""
	@echo "###############################################"
	@echo "The superset is initialised with the user admin@admin.com"
	@echo "Use: 'document.cookie = \"phiphi-user-email=admin@admin.com; Path=/\";' in browser console to set the cookie."
