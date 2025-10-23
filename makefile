# Makefile
.PHONY: help build up down logs clean install dev prod

help: ## Show this help
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "📦 Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ All dependencies installed!"

build: ## Build Docker images
	@echo "🔨 Building Docker images..."
	docker-compose build

up: ## Start all services (production)
	@echo "🚀 Starting services..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "Frontend: http://localhost:6868"
	@echo "Backend: http://localhost:8000"
	@echo "Grafana: http://localhost:3000"
	@echo "Prometheus: http://localhost:9090"

dev: ## Start development environment
	@echo "🔧 Starting development environment..."
	docker-compose -f docker-compose.dev.yml up
	
down: ## Stop all services
	@echo "🛑 Stopping services..."
	docker-compose down
	docker-compose -f docker-compose.dev.yml down

logs: ## Show logs
	docker-compose logs -f

clean: ## Clean up containers, volumes, and images
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Cleanup complete!"

backend-logs: ## Show backend logs
	docker logs -f ai-chat-backend

frontend-logs: ## Show frontend logs
	docker logs -f ai-chat-frontend

backend-shell: ## Open backend shell
	docker exec -it ai-chat-backend bash

frontend-shell: ## Open frontend shell
	docker exec -it ai-chat-frontend sh

restart: ## Restart all services
	@echo "🔄 Restarting services..."
	docker-compose restart

ps: ## Show running containers
	docker-compose ps