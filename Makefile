ENV_FILE ?= ../.env

.PHONY: build up

build:
	docker compose --env-file $(ENV_FILE) build

up:
	docker compose --env-file $(ENV_FILE) up --build
