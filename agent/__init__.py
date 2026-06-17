"""应用层 — Agent 统一智能助手

FAQ检索 + 购物操作，AI自动判断使用哪个工具。
基于 OpenAI 原生 function calling（tools API），零第三方依赖。

公开接口:
    UnifiedAgent  — 统一 Agent，接收聊天消息 + JWT token
"""

from .unified_agent import UnifiedAgent

__all__ = ["UnifiedAgent"]
