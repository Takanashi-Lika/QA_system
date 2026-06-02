"""Embedding 向量化模块 —— RAG 模块内部的独立实体。

负责将文本转换为固定长度的稠密向量。支持两种后端:
  1. 本地模型（sentence-transformers）: 离线可用，无需 API
  2. 在线 API（OpenAI 兼容格式）:   适合大批量或需要更高精度的场景

属性可直接赋值切换后端:
    embed.model_name = "BAAI/bge-large-zh-v1.5"  # 换本地模型
    embed.backend = "api"                          # 切换为 API 模式
"""

import os
from typing import TYPE_CHECKING

import numpy as np

# 为了类型提示，不完全依赖 sentence-transformers
if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class Embedding:
    """文本向量化引擎。

    属性（可直接赋值覆盖）:
        model_name:  模型名（本地: sentence-transformers 模型名; API: embedding 模型名）
        backend:     "local"（默认，sentence-transformers）或 "api"（OpenAI 兼容）
        base_url:    API 端点（仅 backend="api" 时使用）
        api_key:     API 密钥（仅 backend="api" 时使用）

    使用方式:
        embed = Embedding()
        vectors = embed.encode(["文本1", "文本2"])  # → list[list[float]]
    """

    def __init__(
        self,
        model_name: str | None = None,
        backend: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
        self.backend = backend or "local"  # local | api
        self.base_url = base_url or ""     # API 模式时需要
        self.api_key = api_key or ""       # API 模式时需要

        # 懒加载的本地模型实例
        self._local_model: "SentenceTransformer | None" = None

    # ------------------------------------------------------------------
    # 懒加载本地模型
    # ------------------------------------------------------------------

    @property
    def local_model(self) -> "SentenceTransformer":
        """懒加载 sentence-transformers 模型（仅 backend="local" 时使用）。"""
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer(self.model_name)
        return self._local_model

    # ------------------------------------------------------------------
    # 核心方法
    # ------------------------------------------------------------------

    def encode(self, texts: list[str]) -> list[list[float]]:
        """将文本列表编码为向量列表。

        Args:
            texts: 待编码的文本列表

        Returns:
            向量列表，每个向量是 float 列表（维度取决于模型）
        """
        if self.backend == "api":
            return self._encode_api(texts)
        return self._encode_local(texts)

    def _encode_local(self, texts: list[str]) -> list[list[float]]:
        """本地模型编码。"""
        embeddings = self.local_model.encode(texts)
        # sentence-transformers 返回 np.ndarray
        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        return [e.tolist() if isinstance(e, np.ndarray) else list(e) for e in embeddings]

    def _encode_api(self, texts: list[str]) -> list[list[float]]:
        """通过 OpenAI 兼容 API 编码。"""
        from openai import OpenAI

        client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        response = client.embeddings.create(model=self.model_name, input=texts)
        # 按 input 顺序返回
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [d.embedding for d in sorted_data]

    @property
    def dim(self) -> int:
        """返回当前模型的向量维度（用于创建 ChromaDB collection 时指定维度）。"""
        return len(self.encode(["test"])[0])
