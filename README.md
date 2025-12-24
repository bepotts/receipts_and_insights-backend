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
├── venv/                  # Virtual environment (not in git)
├── .env                   # Environment variables (not in git)
├── .env.example           # Environment variables template
├── .gitignore
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` file with your configuration values.

5. Run the application:
   ```bash
   python -m app.main
   ```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app tests
isort app tests
```

### Type Checking
```bash
mypy app
```

## License

MIT

