import os
from model import get_model_client
from rag import get_rag_store


class RetrieverPipeline:
    def __init__(self):
        self._store = get_rag_store()
        self._model = get_model_client()

    @property
    def top_k(self) -> int:
        return int(os.getenv("RAG_TOP_K", "5"))

    @property
    def mode(self) -> str:
        return os.getenv("RETRIEVER_MODE", "hybrid")

    @property
    def rrf_k(self) -> int:
        return int(os.getenv("RETRIEVER_RRF_K", "60"))

    def search(self, query: str, top_k: int | None = None, mode: str | None = None) -> list[dict]:
        return self._store.search(query=query, top_k=top_k or self.top_k, mode=mode or self.mode)

    def answer(self, question: str, top_k: int | None = None) -> dict:
        results = self._store.search(query=question, top_k=top_k or self.top_k, mode=self.mode)

        if not results:
            return {
                "answer": "抱歉，目前FAQ知识库中没有找到相关内容。建议您联系人工客服获取帮助。",
                "sources": [],
            }

        context_parts = []
        for r in results:
            product = r["metadata"].get("product", "未知产品")
            question_faq = r["metadata"].get("question", "")
            answer = ""
            content = r.get("content", "")
            if "\n回答: " in content:
                answer = content.split("\n回答: ", 1)[1]
            context_parts.append(f"【{product}】问: {question_faq}\n答: {answer}")

        context = "\n\n".join(context_parts)

        messages = [
            {
                "role": "system",
                "content": (
                    "你是智居品牌的智能客服助手。请根据以下FAQ知识库内容回答用户问题。"
                    "如果知识库中没有相关信息，请如实告知用户，不要编造答案。"
                    "回答要求：简洁、准确、友好。使用中文回复。"
                ),
            },
            {
                "role": "user",
                "content": f"FAQ知识库:\n\n{context}\n\n用户问题: {question}\n\n请回答:",
            },
        ]

        try:
            answer = self._model.chat(messages)
        except Exception:
            fallback_parts = []
            for i, r in enumerate(results[:3], 1):
                product = r["metadata"].get("product", "")
                q = r["metadata"].get("question", "")
                a = ""
                content = r.get("content", "")
                if "\n回答: " in content:
                    a = content.split("\n回答: ", 1)[1]
                fallback_parts.append(f"{i}.【{product}】问：{q}\n   答：{a}")
            fallback_text = "\n\n".join(fallback_parts)
            answer = f"（AI 模型未配置 API Key，以下为 FAQ 知识库检索结果）\n\n{fallback_text}"

        sources = [
            {
                "product": r["metadata"].get("product", ""),
                "question": r["metadata"].get("question", ""),
                "score": round(r["score"], 4),
            }
            for r in results
        ]

        return {"answer": answer, "sources": sources}
