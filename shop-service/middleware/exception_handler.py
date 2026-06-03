from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common.exceptions import ShopException
from common.context import request_id_var
from common.logger import logger


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(ShopException)
    async def shop_exception_handler(request: Request, exc: ShopException):
        logger.warning(
            "业务异常: %s | code=%d | path=%s",
            exc.message,
            exc.code,
            request.url.path,
        )
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "code": exc.code,
                "message": exc.message,
                "data": None,
                "request_id": request_id_var.get("-"),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            "未预期异常: %s | path=%s",
            str(exc),
            request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "code": 50002,
                "message": "内部服务器错误",
                "data": None,
                "request_id": request_id_var.get("-"),
            },
        )
