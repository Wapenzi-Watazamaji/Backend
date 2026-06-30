# BintiCare

**Python version:** >=3.12
**Package manager:** uv
**Project type:** web-api (FastAPI)

## Getting started

### 1. Set up your virtual environment

Use the provided setup script to create your virtual environment, or do it manually:

```bash
./setup.sh
source .venv/bin/activate
```

*(If you don't have `uv` installed, you can install it via: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`)*

### 2. Install dependencies

The project uses `pyproject.toml` for managing dependencies instead of a `requirements.txt`. Sync your environment to install the project and its dependencies:

```bash
uv sync
```

*(If you need to add a new package, e.g., the `uvicorn` server, use `uv add uvicorn`)*

### 3. Run the project

Start the FastAPI server with live reloading enabled:

```bash
uv run uvicorn app.main:app --reload
```

The API will be accessible at `http://127.0.0.1:8000`. You can view the interactive API documentation at `http://127.0.0.1:8000/docs`.

## License

MIT
