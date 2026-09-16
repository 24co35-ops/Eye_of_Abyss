.PHONY: up down build health logs dev-voiceguard dev-shadowtrace dev-chaineye dev-case-engine frontend frontend-install install-contracts compile-contracts deploy-mumbai generate-data seed demo anchor-test test

COMPOSE := docker-compose -f infrastructure/docker-compose.yml

# ── Docker Compose ─────────────────────────────────────────────────────────
up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

# ── Health checks ──────────────────────────────────────────────────────────
# Services are proxied through nginx on :80 in Docker; direct ports also work.
health:
	@echo "Case Engine:  $$(curl -sf http://localhost:8000/health || echo OFFLINE)"
	@echo "VoiceGuard:   $$(curl -sf http://localhost:8001/health || echo OFFLINE)"
	@echo "ShadowTrace:  $$(curl -sf http://localhost:8002/health || echo OFFLINE)"
	@echo "ChainEye:     $$(curl -sf http://localhost:8003/health || echo OFFLINE)"
	@echo "Via nginx:    $$(curl -sf http://localhost/health/cases  || echo OFFLINE)"

# ── Individual dev servers ─────────────────────────────────────────────────
dev-case-engine:
	cd services/case-engine && uvicorn main:app --reload --port 8000

dev-voiceguard:
	cd services/voiceguard && uvicorn main:app --reload --port 8001

dev-shadowtrace:
	cd services/shadowtrace && uvicorn main:app --reload --port 8002

dev-chaineye:
	cd services/chaineye && uvicorn main:app --reload --port 8003

# ── Frontend ───────────────────────────────────────────────────────────────
frontend:
	cd frontend && npm run dev

frontend-install:
	cd frontend && npm install

# ── Contracts ──────────────────────────────────────────────────────────────
install-contracts:
	cd contracts && npm install

compile-contracts:
	cd contracts && npx hardhat compile

deploy-mumbai:
	cd contracts && npx hardhat run scripts/deploy.ts --network polygonMumbai

# ── Data pipeline & Demo targets ──────────────────────────────────────────
generate-data:
	cd data-pipeline && python main.py generate --count 500 \
		--archetypes investment_fraudster darknet_vendor ransomware_operator \
		--output-dir ./output

seed:
	python scripts/seed.py

demo:
	python scripts/demo_pipeline.py

anchor-test:
	python scripts/anchor_test.py

test:
	pytest -v

