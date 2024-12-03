LOGS = docker-compose.logs.yml 

MICROSERVICES = docker-compose.microservices.yml

start-logs:
	docker compose -f $(LOGS) up -d

restart-logs:
	docker compose -f $(LOGS) restart

start-microservices:
	docker compose -f $(MICROSERVICES) up -d

restart-microservices:
	docker compose -f $(MICROSERVICES) restart

build-all:
	docker compose -f $(LOGS) -f $(MICROSERVICES) up --build -d

build-logs:
	docker compose -f $(LOGS) up --build -d

build-microservices:
	docker compose -f $(MICROSERVICES) up --build -d