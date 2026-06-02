"""基础层 — RAG 向量存储模块

将本地 FAQ 文档向量化并存入向量数据库，对外提供写入和检索能力。
只负责"存"和"查"，不涉及文本生成。

公开接口:
    RAGStore    — 向量入库 + 检索（dense / sparse / hybrid）
    get_rag_store — 模块级单例
"""

from .store import RAGStore, get_rag_store

__all__ = ["RAGStore", "get_rag_store"]
