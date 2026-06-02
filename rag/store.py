"""RAG 存储模块 —— 文档入库、向量存储与多模式检索。

把 parser、embedding、bm25、chromadb 组合为一个统一入口。
只负责"存"和"查"，不涉及任何文本生成。

使用方式:
    store = RAGStore()
    store.build_index()
    results = store.search("摄像头怎么连WiFi", mode="hybrid")
"""

import os
from pathlib import Path

import chromadb

from .parser import parse_all_files, Chunk
from .embedding import Embedding
from .bm25 import Bm25Retriever


class RAGStore:
    """RAG 向量存储 — 文档入库 + 多模式检索。

    属性（可直接赋值覆盖默认值）:
        resource_dir:   原始 FAQ 文档目录
        db_dir:         ChromaDB 持久化目录
        collection_name: ChromaDB collection 名称
        top_k:          默认检索返回数
        bm25_k1:        BM25 词频饱和系数
        bm25_b:         BM25 长度归一化系数
        embedding:      Embedding 实例（可替换模型）
    """

    def __init__(
        self,
        resource_dir: str | None = None,
        db_dir: str | None = None,
        collection_name: str | None = None,
        top_k: int | None = None,
        bm25_k1: float | None = None,
        bm25_b: float | None = None,
    ):
        # 属性配置: 参数 > 环境变量 > 默认值
        self.resource_dir = resource_dir or os.getenv("RAG_RESOURCE_DIR", "rag_resource")
        self.db_dir = db_dir or os.getenv("RAG_DB_DIR", "rag_db")
        self.collection_name = collection_name or os.getenv("RAG_COLLECTION_NAME", "faq")
        self.top_k = top_k or int(os.getenv("RAG_TOP_K", "5"))
        self.bm25_k1 = bm25_k1 or float(os.getenv("RAG_BM25_K1", "1.5"))
        self.bm25_b = bm25_b or float(os.getenv("RAG_BM25_B", "0.75"))

        # 子组件
        self.embedding = Embedding()
        self.bm25 = Bm25Retriever(k1=self.bm25_k1, b=self.bm25_b)

        # ChromaDB 客户端
        self._client = chromadb.PersistentClient(path=str(self.db_dir))

        # BM25 索引与 chunk 的映射（内存中，需每次启动重建）
        self._chunks_snapshot: list[Chunk] = []

    # ==================================================================
    # 索引构建
    # ==================================================================

    def build_index(self, force: bool = False) -> int:
        """解析文档、构建向量索引 + BM25 索引。

        ChromaDB 有持久化，BM25 每次启动重建。
        """
        collection = self._get_or_create_collection()

        # 1. 解析 FAQ 文档
        chunks = parse_all_files(Path(self.resource_dir))
        if not chunks:
            return 0

        texts = [c.content for c in chunks]

        # 2. Dense 索引: 只在首次或 force 时写入 ChromaDB
        if force or collection.count() == 0:
            if force and collection.count() > 0:
                existing_ids = collection.get()["ids"]
                if existing_ids:
                    collection.delete(ids=existing_ids)

            embeddings = self.embedding.encode(texts)
            metadatas = [c.metadata for c in chunks]

            collection.add(
                ids=[c.id for c in chunks],
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

        # 3. Sparse 索引: 每次启动都重建（BM25 仅内存，无持久化）
        self.bm25.build(texts)
        self._chunks_snapshot = chunks

        return len(chunks)

    # ==================================================================
    # 检索 — 三种模式
    # ==================================================================

    def search(
        self,
        query: str,
        top_k: int | None = None,
        mode: str | None = None,
    ) -> list[dict]:
        """统一检索入口。

        Args:
            query:  用户查询文本
            top_k:  返回结果数（默认用属性值）
            mode:   dense | sparse | hybrid

        Returns:
            [{id, content, metadata, score, source}, ...]
        """
        top_k = top_k or self.top_k
        mode = mode or "hybrid"

        if mode == "dense":
            return self._search_dense(query, top_k)
        elif mode == "sparse":
            return self._search_sparse(query, top_k)
        elif mode == "hybrid":
            return self._search_hybrid(query, top_k)
        else:
            raise ValueError(f"不支持的模式: {mode}，可选 dense/sparse/hybrid")

    # ------------------------------------------------------------------
    # Dense — 向量语义检索
    # ------------------------------------------------------------------

    def _search_dense(self, query: str, top_k: int) -> list[dict]:
        collection = self._get_or_create_collection()
        if collection.count() == 0:
            return []

        query_embedding = self.embedding.encode([query])
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        formatted = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                formatted.append(
                    {
                        "id": chunk_id,
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": round(1 - results["distances"][0][i], 4),
                        "source": "dense",
                    }
                )
        return formatted

    # ------------------------------------------------------------------
    # Sparse — BM25 关键词检索
    # ------------------------------------------------------------------

    def _search_sparse(self, query: str, top_k: int) -> list[dict]:
        if self.bm25.N == 0:
            return []

        results = self.bm25.search(query, top_k=top_k)
        formatted = []
        for idx, score in results:
            chunk = self._chunks_snapshot[idx]
            formatted.append(
                {
                    "id": chunk.id,
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "score": score,
                    "source": "sparse",
                }
            )
        return formatted

    # ------------------------------------------------------------------
    # Hybrid — RRF 融合
    # ------------------------------------------------------------------

    def _search_hybrid(self, query: str, top_k: int) -> list[dict]:
        rrf_k = int(os.getenv("RETRIEVER_RRF_K", "60"))  # RRF 平滑参数

        candidate_k = top_k * 2
        dense_results = self._search_dense(query, candidate_k)
        sparse_results = self._search_sparse(query, candidate_k)

        # RRF 分数计算
        rrf_scores: dict[str, float] = {}
        result_map: dict[str, dict] = {}

        for rank, item in enumerate(dense_results, start=1):
            cid = item["id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0) + 1.0 / (rrf_k + rank)
            result_map[cid] = item

        for rank, item in enumerate(sparse_results, start=1):
            cid = item["id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0) + 1.0 / (rrf_k + rank)
            if cid not in result_map:
                result_map[cid] = item

        sorted_ids = sorted(rrf_scores, key=lambda k: rrf_scores[k], reverse=True)[:top_k]

        formatted = []
        for cid in sorted_ids:
            item = result_map[cid]
            formatted.append(
                {
                    "id": cid,
                    "content": item["content"],
                    "metadata": item["metadata"],
                    "score": round(rrf_scores[cid], 6),
                    "source": "hybrid",
                }
            )
        return formatted

    # ==================================================================
    # 统计
    # ==================================================================

    def get_stats(self) -> dict:
        """返回当前索引的统计信息。"""
        collection = self._get_or_create_collection()
        count = collection.count()
        products = set()
        if count > 0:
            metadatas = collection.get(include=["metadatas"])["metadatas"]
            for m in metadatas:
                products.add(m.get("product", "unknown"))
        return {
            "total_chunks": count,
            "bm25_docs": self.bm25.N,
            "products": sorted(products),
            "embedding_model": self.embedding.model_name,
        }

    # ==================================================================
    # 内部
    # ==================================================================

    def _get_or_create_collection(self):
        """获取或创建 ChromaDB collection（余弦距离）。"""
        return self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )


# ---------------------------------------------------------------------------
# 模块级单例
# ---------------------------------------------------------------------------

_rag_store: RAGStore | None = None


def get_rag_store() -> RAGStore:
    """获取 RAGStore 模块级单例。"""
    global _rag_store
    if _rag_store is None:
        _rag_store = RAGStore()
    return _rag_store
