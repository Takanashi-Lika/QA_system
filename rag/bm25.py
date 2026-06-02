"""BM25 关键词检索引擎 —— Sparse Retrieval（稀疏检索）。

与 Dense Retrieval（向量语义检索）互补：
  - Dense: 理解语义相似（"没电" ≈ "电量低"），但可能跨主题误召回
  - Sparse: 精确关键词匹配（"摄像头" 必须命中文档中的 "摄像头"），不会跑偏

BM25 是 TF-IDF 的改进版，核心改进：
  1. 词频饱和: 一个词出现 100 次不会得到 100 倍的分数
  2. 文档长度归一化: 长文档不会因为词多而天然占优

公式（逐项拆解见代码注释）:
  BM25(d, q) = Σ IDF(t) * [f(t,d)·(k1+1)] / [f(t,d) + k1·(1-b + b·|d|/avgdl)]
                t∈q

参考: Robertson & Zaragoza (2009), "The Probabilistic Relevance Framework: BM25 and Beyond"
"""

import math
from collections import defaultdict


class Bm25Retriever:
    """BM25 关键词检索器。

    使用方式:
        bm25 = Bm25Retriever(k1=1.5, b=0.75)
        bm25.build(corpus=["文档A的文本", "文档B的文本", ...])
        results = bm25.search("查询关键词", top_k=5)
        # results: [(doc_index, bm25_score), ...]
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

        self.corpus: list[str] = []
        self.doc_freqs: dict[str, int] = defaultdict(int)
        self.doc_tfs: list[dict[str, int]] = []
        self.avgdl: float = 0.0
        self.N: int = 0

    def build(self, corpus: list[str]) -> None:
        """构建 BM25 索引。"""
        import jieba

        self.corpus = corpus
        self.N = len(corpus)
        self.doc_freqs = defaultdict(int)
        self.doc_tfs = []
        total_length = 0

        for doc_text in corpus:
            tokens = list(jieba.cut(doc_text))
            tf = defaultdict(int)
            for token in tokens:
                token = token.strip()
                if token and token not in (" ", "\n", ""):
                    tf[token] += 1
            self.doc_tfs.append(dict(tf))
            total_length += len(tokens)

            for token in set(tf.keys()):
                self.doc_freqs[token] += 1

        self.avgdl = total_length / max(self.N, 1)

    def search(self, query: str, top_k: int = 5) -> list[tuple[int, float]]:
        """BM25 检索，返回 [(doc_index, score), ...] 按分数降序。"""
        import jieba

        if self.N == 0:
            return []

        query_tokens = list(jieba.cut(query))
        query_terms = [t.strip() for t in query_tokens if t.strip()]

        scores = []
        for idx, tf in enumerate(self.doc_tfs):
            score = self._bm25_score(query_terms, tf, len(self.corpus[idx]))
            if score > 0:
                scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _bm25_score(self, query_terms: list[str], tf: dict[str, int], doc_len: int) -> float:
        """计算单个文档的 BM25 总分。"""
        score = 0.0

        for term in set(query_terms):
            f = tf.get(term, 0)
            if f == 0:
                continue

            # IDF: 逆文档频率 — 词越稀有，区分度越大
            n = self.doc_freqs.get(term, 0)
            idf = math.log((self.N - n + 0.5) / (n + 0.5) + 1)

            # TF 饱和: 词频高不会无限加分
            numerator = f * (self.k1 + 1)
            denominator = f + self.k1 * (1 - self.b + self.b * doc_len / max(self.avgdl, 1))
            tf_saturated = numerator / denominator

            score += idf * tf_saturated

        return round(score, 6)
