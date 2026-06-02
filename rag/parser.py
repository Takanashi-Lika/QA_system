"""文档解析模块 —— 将原始 FAQ 文档拆分为可检索的文本块（Chunk）。

RAG 的第一步：把知识库中的文档解析成结构化的文本片段。
每个片段会携带元数据（产品名、来源文件等），方便检索时溯源。
"""

import re
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """RAG 中最小的检索单元 —— 一个文本片段 + 它的元数据。

    属性:
        id:      唯一标识，用于在向量数据库中定位
        content: 会被向量化的文本内容（即后续用来计算相似度的文字）
        metadata: 附加信息，如产品名、来源文件、问题原文等
                  检索时不会参与相似度计算，但可以用来过滤或展示来源
    """

    id: str
    content: str
    metadata: dict = field(default_factory=dict)


def parse_faq_file(filepath: Path) -> list[Chunk]:
    """解析单个 FAQ Markdown 文件，返回该文件的所有 Q&A Chunk。

    FAQ 文件的格式约定：
        **问题标题**
        回答内容（可多行）

    每个 Q&A 对会被合并为一个 Chunk，content 格式化为：
        "产品: xxx\n问题: xxx\n回答: xxx"
    """
    text = filepath.read_text(encoding="utf-8")
    product_name = _extract_product_name(filepath.stem)

    blocks = _split_into_qa_blocks(text)

    chunks = []
    for i, (question, answer) in enumerate(blocks):
        chunk_id = f"{filepath.stem}_{i}"
        chunks.append(
            Chunk(
                id=chunk_id,
                content=f"产品: {product_name}\n问题: {question}\n回答: {answer}",
                metadata={
                    "source": filepath.name,
                    "product": product_name,
                    "question": question,
                    "chunk_index": i,
                },
            )
        )
    return chunks


def parse_all_files(resource_dir: Path) -> list[Chunk]:
    """遍历 resource_dir 下所有 .md 文件，合并解析结果。"""
    all_chunks = []
    for filepath in sorted(resource_dir.glob("*.md")):
        all_chunks.extend(parse_faq_file(filepath))
    return all_chunks


def _split_into_qa_blocks(text: str) -> list[tuple[str, str]]:
    """将 Markdown 文本拆分为 (问题, 回答) 元组的列表。

    算法说明：
        1. 按行扫描，遇到 **粗体** 行视为问题标题
        2. 问题的后续行（直到下一个问题或文件末尾）视为回答内容
        3. 跳过没有回答内容的问题
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    qa_pairs = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("**") and line.count("**") >= 2:
            question = line.strip("*").strip()
            i += 1
            answer_lines = []
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith("**") and next_line.count("**") >= 2:
                    break
                if next_line:
                    answer_lines.append(next_line)
                i += 1
            answer = " ".join(answer_lines).strip()
            if answer:
                qa_pairs.append((question, answer))
        else:
            i += 1

    return qa_pairs


def _extract_product_name(filename_stem: str) -> str:
    """从文件名提取产品名称。

    Examples:
        Doc1-X1智能门锁FAQ → X1智能门锁
        Doc5-售后与保修政策 → 售后与保修政策
    """
    name = re.sub(r"^Doc\d+-", "", filename_stem)
    name = re.sub(r"FAQ$", "", name, flags=re.IGNORECASE)
    return name or filename_stem
