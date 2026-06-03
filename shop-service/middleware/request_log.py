import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from common.logger import logger


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed_ms = (time.time() - start) * 1000
        logger.info(
            "%s %s -> %d | %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
