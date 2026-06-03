import json
import os
import threading

import redis

from common.logger import logger

_client: redis.Redis | None = None


def init_redis():
    global _client
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL 环境变量未设置")

    _client = redis.Redis.from_url(redis_url)
    logger.info("Redis 客户端已初始化")


def get_cache(key: str) -> dict | None:
    if _client is None:
        logger.warning("Redis 客户端未初始化，无法读取缓存 key=%s", key)
        return None
    try:
        data = _client.get(key)
        if data is None:
            return None
        return json.loads(data)
    except Exception:
        logger.warning("读取缓存失败，降级处理 key=%s", key, exc_info=True)
        return None


def set_cache(key: str, data, ttl: int):
    if _client is None:
        logger.warning("Redis 客户端未初始化，无法写入缓存 key=%s", key)
        return
    try:
        _client.setex(key, ttl, json.dumps(data, ensure_ascii=False))
    except Exception:
        logger.warning("写入缓存失败 key=%s", key, exc_info=True)


def delete_cache(key: str):
    if _client is None:
        return
    try:
        _client.delete(key)
    except Exception:
        logger.warning("删除缓存失败 key=%s", key, exc_info=True)


def delete_keys(*keys: str):
    if _client is None:
        return
    try:
        pipe = _client.pipeline()
        for key in keys:
            pipe.delete(key)
        pipe.execute()
    except Exception:
        logger.warning("批量删除缓存失败 keys=%s", keys, exc_info=True)


class CacheLocks:
    _locks: dict[str, threading.Lock] = {}

    @classmethod
    def acquire(cls, key: str) -> threading.Lock:
        if key not in cls._locks:
            cls._locks[key] = threading.Lock()
        return cls._locks[key]


def close_redis():
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("Redis 客户端已关闭")
