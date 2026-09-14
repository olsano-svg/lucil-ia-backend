import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """
    Registro estructurado de errores y monitoreo. 
    Evita exponer detalles sensibles del stacktrace al cliente.
    """
    logger.error(
        f"Unhandled exception at {request.url.path} - Method: {request.method} - Error: {str(exc)}",
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )
