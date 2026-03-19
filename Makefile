ENV_FILE ?= ../.env-dev

.PHONY: build up

### --- FOR DEVELOPMENT --- 
build:
	docker compose --env-file $(ENV_FILE) build

build-up:
	docker compose --env-file $(ENV_FILE) up --build

up:
	docker compose --env-file $(ENV_FILE) up

### --- FOR PRODUCTION ----
build-prod:
	docker build --target production --platform linux/amd64 --tag southamerica-west1-docker.pkg.dev/mezivus-test/mezivus-test-repository/mi-api:production .

push-prod:
	docker push southamerica-west1-docker.pkg.dev/mezivus-test/mezivus-test-repository/mi-api:production