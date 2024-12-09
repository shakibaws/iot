LOGS = docker-compose.logs.yml 
MICROSERVICES = docker-compose.microservices.yml
LOGS_PATH=logs


start-logs:
	docker compose -f $(LOGS) up -d

restart-logs:
	docker compose -f $(LOGS) restart

start-microservices:
	docker compose -f $(MICROSERVICES) up -d

restart-microservices:
	docker compose -f $(MICROSERVICES) restart

stop-microservices:
	docker compose -f $(MICROSERVICES) down

build-all:
	docker compose -f $(LOGS) -f $(MICROSERVICES) up --build -d

build-logs:
	docker compose -f $(LOGS) up --build -d

build-microservices:
	docker compose -f $(MICROSERVICES) up --build -d

clean:
	docker compose -f $(LOGS) -f $(MICROSERVICES) down
	@echo "Cleaning up log and error files..."
	@sudo find $(LOGS_PATH) -type f \( -name '*.log' -o -name '*.err' \) -exec rm -f {} +
	@echo "Cleanup complete!"