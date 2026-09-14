import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api_router import api_router
from app.db.init_db import init_tables

# Configuración básica de logging y monitoreo
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación: asegura que la base de datos local esté lista."""
    await init_tables()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API Core para Lucil AI - Next Gen Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Seguridad: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para registro de errores y monitoreo básico."""
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Error procesando la petición: {str(e)}", exc_info=True)
        raise

@app.get("/health")
async def health_check():
    """Endpoint para monitoreo de salud del sistema."""
    return {"status": "ok", "version": "1.0.0"}

# TODO: Incluir routers (api_router) aquí
