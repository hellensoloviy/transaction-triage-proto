# Transaction Triage System
# All commands the reviewer will run are defined here

.PHONY: up down seed day-run night-run test verify clean

# ── Infrastructure ─────────────────────────────────────────────────────────

up:
	docker compose up -d
	@echo "Waiting for Postgres to be ready..."
	@sleep 3
	@pip install -r requirements.txt -q
	@echo "Starting FastAPI service..."
	@uvicorn app.main:app --host 0.0.0.0 --port 8000 &
	@sleep 2
	@echo "✓ System is up. API at http://localhost:8000"

down:
	docker compose down
	@pkill -f "uvicorn app.main" || true
	@echo "✓ System stopped"

# ── Data ───────────────────────────────────────────────────────────────────

seed:
	@echo "Seeding database with 200 transactions (seed=17)..."
	python seed/seeder.py
	@echo "✓ Database seeded"

# ── Agents ────────────────────────────────────────────────────────────────

day-run:
	@echo "Running Day Agent..."
	python agents/day.py
	@echo "✓ Day Agent complete"

night-run:
	@echo "Running Night Agent..."
	python agents/night.py
	@echo "✓ Night Agent complete. Check reports/morning-report.md"

# ── Quality ───────────────────────────────────────────────────────────────

test:
	@echo "Running tests..."
	pytest tests/ -v
	@echo "✓ Tests complete"

verify:
	@echo "Running verification suite..."
	python tests/verify.py
	@echo "✓ Verification complete"

# ── Cleanup ───────────────────────────────────────────────────────────────

clean:
	docker compose down -v
	@pkill -f "uvicorn app.main" || true
	@rm -rf reports/*.md
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Clean complete"