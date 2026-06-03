import os
from contextlib import contextmanager

from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor

from common.logger import logger

_pool: ThreadedConnectionPool | None = None


def init_pool():
    global _pool
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL 环境变量未设置")

    _pool = ThreadedConnectionPool(
        minconn=2,
        maxconn=10,
        dsn=database_url,
        options="-c search_path=shop",
    )
    logger.info("数据库连接池已创建: minconn=2, maxconn=10, search_path=shop")


def get_connection():
    if _pool is None:
        raise RuntimeError("连接池未初始化，请先调用 init_pool()")
    return _pool.getconn()


def release_connection(conn):
    if _pool is None:
        raise RuntimeError("连接池未初始化，请先调用 init_pool()")
    _pool.putconn(conn)


@contextmanager
def get_cursor():
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_connection(conn)


def close_pool():
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
        logger.info("数据库连接池已关闭")
