import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.logger import setup_logger, logger
from infrastructure.database import init_pool, close_pool
from infrastructure.redis_client import init_redis, close_redis
from infrastructure.scheduler import start_scheduler, shutdown_scheduler, register_job
from middleware.request_id import RequestIDMiddleware
from middleware.request_log import RequestLogMiddleware
from middleware.exception_handler import register_exception_handlers

from domain.order.order_service import cancel_timeout_orders

from apps.c_endpoint.user.router import router as user_router
from apps.c_endpoint.product.router import router as c_product_router
from apps.c_endpoint.cart.router import router as cart_router
from apps.c_endpoint.order.router import router as c_order_router
from apps.c_endpoint.logistics.router import router as logistics_router
from apps.c_endpoint.after_sale.router import router as after_sale_router

from apps.b_endpoint.category.router import router as category_router
from apps.b_endpoint.product.router import router as b_product_router
from apps.b_endpoint.order.router import router as b_order_router
from apps.b_endpoint.after_sale.router import router as b_after_sale_router

from apps.internal.router import router as internal_router

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    logger.info("===== 应用启动中 =====")
    init_pool()
    init_redis()
    register_job(cancel_timeout_orders, interval_minutes=5)
    start_scheduler()
    logger.info("===== 应用启动完成 =====")
    yield
    logger.info("===== 应用关闭中 =====")
    shutdown_scheduler()
    close_redis()
    close_pool()
    logger.info("===== 应用已关闭 =====")


app = FastAPI(
    title="电商平台 - Shop Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(user_router)
app.include_router(c_product_router)
app.include_router(cart_router)
app.include_router(c_order_router)
app.include_router(logistics_router)
app.include_router(after_sale_router)

app.include_router(category_router)
app.include_router(b_product_router)
app.include_router(b_order_router)
app.include_router(b_after_sale_router)

app.include_router(internal_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
