import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from retriever import RetrieverPipeline
from agent import ShoppingAgent


class SearchRequest(BaseModel):
    question: str
    top_k: int | None = None
    mode: str | None = None


class SearchResponse(BaseModel):
    answer: str
    sources: list[dict]


class AgentChatRequest(BaseModel):
    messages: list[dict]
    user_token: str = ""


class AgentChatResponse(BaseModel):
    response: str
    tool_calls: list[dict] = []


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG 智能客服 API",
        version="1.1.0",
        description="FAQ 知识库检索 + LLM 生成回复 + Agent 智能购物",
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

    @app.post("/api/agent/chat", response_model=AgentChatResponse)
    def agent_chat(body: AgentChatRequest):
        if not body.user_token:
            return AgentChatResponse(
                response="请先在商城登录，然后将 JWT Token 粘贴到输入框上方的「用户Token」栏。没有 Token 无法操作购物车和下单哦。",
                tool_calls=[],
            )
        agent = ShoppingAgent(body.user_token)
        result = agent.chat(body.messages)
        return AgentChatResponse(**result)

    return app
