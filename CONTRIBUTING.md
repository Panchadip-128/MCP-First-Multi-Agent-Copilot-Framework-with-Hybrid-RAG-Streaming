# Contributing to LLM Copilot Framework

Thank you for your interest in contributing! This project is being developed for Google Summer of Code 2026.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/llm-copilot-framework.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `poetry run pytest`
6. Commit your changes: `git commit -m "Add some feature"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

### Backend
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### With Docker
```bash
docker-compose up -d
```

## Code Style

- **Python**: Follow PEP 8, use Black for formatting
- **TypeScript**: Follow Airbnb style guide, use ESLint
- **Commits**: Use conventional commits format

## Testing

```bash
# Backend tests
cd backend
poetry run pytest

# Type checking
poetry run mypy .

# Linting
poetry run ruff check .
```

## Project Structure

```
backend/
  app/
    core/          # Core services (MCP, RAG, LLM Router)
    api/           # API endpoints
    agents/        # Tool agents
    models/        # Data models
    utils/         # Utilities

frontend/
  src/
    components/    # React components
    pages/         # Page components
    lib/           # Utilities and API client
```

## Adding New Features

### Adding a Tool Agent

1. Create a new file in `backend/app/agents/`
2. Implement the tool interface
3. Register it in MCP protocol
4. Add tests

### Adding API Endpoints

1. Create endpoint in `backend/app/api/endpoints/`
2. Add to router in `app/api/routes.py`
3. Update frontend API client

## Questions?

Open an issue or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
