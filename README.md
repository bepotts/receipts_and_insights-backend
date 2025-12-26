# Receipts and Insights Backend

Backend API for the Receipts and Insights application.

## Project Structure

```
backend/
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py            # Application entry point
│   ├── config.py          # Configuration management
│   ├── api/               # API routes
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/  # API endpoints
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   └── security.py    # Authentication, security
│   ├── models/            # Database models
│   │   └── __init__.py
│   ├── schemas/           # Pydantic schemas
│   │   └── __init__.py
│   ├── services/          # Business logic
│   │   └── __init__.py
│   └── utils/             # Utility functions
│       └── __init__.py
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── conftest.py        # Pytest configuration
│   └── test_*.py          # Test files
├── .venv/                 # Virtual environment (created by Poetry, not in git)
├── .env                   # Environment variables (not in git)
├── .env.example           # Environment variables template
├── .gitignore
├── poetry.lock            # Poetry lock file (dependency versions)
├── requirements.txt       # Python dependencies (exported from Poetry)
├── pyproject.toml         # Project configuration (Poetry, pytest, etc.)
└── README.md              # This file
```

## Setup

This project uses [Poetry](https://python-poetry.org/) for dependency management. Poetry provides a better way to manage Python dependencies and virtual environments.

### Install Poetry

If you don't have Poetry installed, follow the [official installation guide](https://python-poetry.org/docs/#installation):

```bash
# Using the official installer (recommended)
curl -sSL https://install.python-poetry.org | python3 -
```

Or using pip (not recommended for production):
```bash
pip install poetry
```

### Project Setup

1. Install dependencies (Poetry will create a virtual environment automatically):
   ```bash
   poetry install
   ```

2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` file with your configuration values.

4. Run the application:
   ```bash
   # Using Poetry
   poetry run python -m app.main
   
   # Or using the Poetry script
   poetry run start
   
   # Or using poe (poethepoet) if installed
   poe start
   ```

### Using Poetry

**Activate the virtual environment:**
```bash
poetry shell
```

**Run commands within the Poetry environment:**
```bash
poetry run <command>
```

**Add a new dependency:**
```bash
poetry add <package-name>
```

**Add a development dependency:**
```bash
poetry add --group dev <package-name>
```

**Update dependencies:**
```bash
poetry update
```

**Export requirements.txt (if needed):**
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

## Development

### Running Tests
```bash
# Using Poetry
poetry run pytest

# Or using poe (poethepoet)
poe test

# If virtual environment is activated
pytest
```

### Code Formatting
```bash
# Using Poetry
poetry run black app tests
poetry run isort app tests

# Or if virtual environment is activated
black app tests
isort app tests
```

### Linting
```bash
# Using Poetry
poetry run ruff check .

# Or using poe (poethepoet)
poe lint

# If virtual environment is activated
ruff check .
```

### Type Checking
```bash
# Using Poetry
poetry run mypy app

# If virtual environment is activated
mypy app
```

### Available Poe Tasks

This project uses [poethepoet](https://github.com/nat-n/poethepoet) (poe) for task automation. After installing dependencies with Poetry, you can use:

- `poe start` - Start the development server with auto-reload
- `poe test` - Run the test suite
- `poe lint` - Run linting checks

## License

MIT

