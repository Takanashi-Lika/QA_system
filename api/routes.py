import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from retriever import RetrieverPipeline
from agent.unified_agent import UnifiedAgent


class SearchRequest(BaseModel):
    question: str
    top_k: int | None = None
    mode: str | None = None


class SearchResponse(BaseModel):
    answer: str
    sources: list[dict]


class UnifiedChatRequest(BaseModel):
    messages: list[dict]
    user_token: str = ""


class UnifiedChatResponse(BaseModel):
    response: str
    tool_calls: list[dict] = []


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG 智能客服 API",
        version="1.2.0",
        description="统一智能对话：FAQ检索 + Agent购物 + LLM自动选工具",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    pipeline = RetrieverPipeline()

    @app.on_event("startup")
    def _startup():
        pipeline._store.build_index()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/chat", response_model=SearchResponse)
    def chat(body: SearchRequest):
        result = pipeline.answer(body.question, top_k=body.top_k)
        return SearchResponse(**result)

    @app.post("/api/search")
    def search(body: SearchRequest):
        results = pipeline.search(body.question, top_k=body.top_k, mode=body.mode)
        return {"results": results, "total": len(results)}

    @app.get("/api/stats")
    def stats():
        s = pipeline._store.get_stats()
        return s

    @app.post("/api/chat/unified", response_model=UnifiedChatResponse)
    def unified_chat(body: UnifiedChatRequest):
        agent = UnifiedAgent(body.user_token)
        result = agent.chat(body.messages)
        return UnifiedChatResponse(**result)

    return app
