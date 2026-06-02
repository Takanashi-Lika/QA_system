"""应用层 — API 接口服务

对外暴露统一的 HTTP 检索接口，通过参数控制是否启用查询改写。
只依赖 retriever 模块，不直接访问 model 或 rag。

公开接口:
    create_app  — 创建 FastAPI 应用实例
"""

from .routes import create_app

__all__ = ["create_app"]
