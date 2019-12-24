.PHONY: build

run:
	docker-compose -f deployment/docker-compose.yaml up --build -d

stop:
	docker-compose -f deployment/docker-compose.yaml down

restart: stop run

