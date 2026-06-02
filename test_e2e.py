"""
端到端测试：用户问题 → RAG 检索 → LLM 生成回复

运行前请确保 .env 中 MODEL_API_KEY 已填写正确的 API Key。
"""

from dotenv import load_dotenv
load_dotenv()

from rag import get_rag_store
from model import get_model_client


def test_e2e(question: str, top_k: int = 3):
    """完整 RAG 流程：检索 + 生成"""

    # ── 1. RAG 检索 ──
    print(f"\n{'='*60}")
    print(f"用户问题: {question}")
    print(f"{'='*60}")

    store = get_rag_store()
    store.build_index()  # 确保 BM25 就绪

    results = store.search(question, top_k=top_k, mode="hybrid")
    if not results:
        print("未检索到相关内容。")
        return

    print(f"\n检索到 {len(results)} 条相关 FAQ:\n")
    context_parts = []
    for i, r in enumerate(results, 1):
        product = r["metadata"]["product"]
        question_faq = r["metadata"]["question"]
        answer = ""
        if "\n回答: " in r["content"]:
            answer = r["content"].split("\n回答: ", 1)[1]

        print(f"  [{i}] [{r['source']}] {product} — {question_faq}")
        print(f"      回答: {answer[:80]}{'...' if len(answer) > 80 else ''}")
        print(f"      分数: {r['score']}")
        context_parts.append(f"【{product}】问: {question_faq}\n答: {answer}")

    # ── 2. 调用 LLM 生成回复 ──
    context = "\n\n".join(context_parts)

    system_prompt = (
        "你是智居品牌的智能客服助手。请根据以下FAQ知识库内容回答用户问题。"
        "如果知识库中没有相关信息，请如实告知用户，不要编造答案。"
        "回答要求：简洁、准确、友好。"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"FAQ知识库:\n\n{context}\n\n用户问题: {question}\n\n请回答:"},
    ]

    print(f"\n{'='*60}")
    print("LLM 回复:")
    print(f"{'='*60}")

    client = get_model_client()
    try:
        response = client.chat(messages)
        print(response)
    except Exception as e:
        print(f"LLM 调用失败: {e}")
        print("请检查 .env 中 MODEL_API_KEY 是否正确。")


if __name__ == "__main__":
    import sys
    question = sys.argv[1] if len(sys.argv) > 1 else "门锁没电了怎么办"
    test_e2e(question)
