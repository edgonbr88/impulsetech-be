from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API REST de la plataforma de gestión operativa y comercial de ImpulseTech.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar y registrar routers de módulos
from src.modules.auth.router import router as auth_router
from src.modules.users.router import router as users_router
from src.modules.clients.router import router as clients_router
from src.modules.leads.router import router as leads_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(clients_router, prefix="/api/v1")
app.include_router(leads_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"{settings.PROJECT_NAME} is running.",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
