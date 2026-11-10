# ImpulseTech Backend (`impulsetech-be`)

Backend REST API para la plataforma operativa y comercial de ImpulseTech, desarrollado con Python 3.12+, FastAPI, SQLAlchemy 2.0 Async, Pydantic v2 y seguridad JWT.

## Requisitos
- Python 3.12+
- Docker y Docker Compose
- PostgreSQL 16

## Ejecución Local
```bash
# Con Docker Compose desde la raíz del proyecto
docker compose up backend

# O de forma independiente
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

## Pruebas
```bash
pytest tests/
```
