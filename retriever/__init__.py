"""领域层 — Retriever 检索增强编排模块

组合 Model 的查询改写能力与 RAG 的向量检索能力，编排检索增强全流程。
只通过 model 和 rag 的 __init__.py 导出进行调用，不直连内部文件。

公开接口:
    RetrieverPipeline  — 查询改写 + 混合检索一站式入口
"""

from .pipeline import RetrieverPipeline

__all__ = ["RetrieverPipeline"]
