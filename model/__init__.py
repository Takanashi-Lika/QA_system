"""基础层 — Model 文本生成模块

提供统一的 LLM 调用能力：同步/流式对话、提示词模板、重试与异常处理。
只负责文本生成，不涉及 Embedding。

公开接口:
    ModelClient  — 模块级单例，对外暴露 chat / chat_stream / format_prompt
"""

from .client import ModelClient, get_model_client

__all__ = ["ModelClient", "get_model_client"]
