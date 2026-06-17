"""应用层 — Agent 智能购物助手

通过自然语言驱动后端 API：商品搜索、加入购物车、下单、支付。
基于 LangChain 工具调用（function calling），LLM 自动编排多步骤操作。

公开接口:
    ShoppingAgent  — 购物 Agent，接收用户消息 + JWT token，返回工具调用结果
"""

from .agent import ShoppingAgent

__all__ = ["ShoppingAgent"]
