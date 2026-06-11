# Run the cv-coach agent locally as a CLI
run:
    cd cv-coach && uv run python main.py

# Run the CV Studio agent API (used by the fe)
serve:
    cd cv-coach && uv run uvicorn server:app --reload --port 8000

# Serve the CV Studio frontend
fe:
    cd fe && python3 -m http.server 5500

# Build and run the full stack via docker compose, then open the FE
up-all:
    docker compose -f dockercompose.yml up --build -d
    xdg-open http://localhost:5500
    docker compose -f dockercompose.yml logs -f

# Install/sync project dependencies
sync:
    cd cv-coach && uv sync
