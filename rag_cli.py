"""
RAG 数据库 — 主入口（临时 CLI，后续由 api/ 模块替代）

功能：
  1. 将 rag_resource/ 下的 FAQ 文档入库（构建索引）
  2. 交互式语义检索 — 支持三种模式:
       dense:  纯向量语义检索
       sparse: BM25 关键词检索
       hybrid: RRF 融合检索（默认推荐）

配置: .env 文件（MODEL_* / EMBEDDING_* / RAG_* 前缀隔离）
"""

import argparse
from dotenv import load_dotenv

from rag import RAGStore


_current_mode: str | None = None


def cmd_build(store: RAGStore, args) -> None:
    force = args.force
    print(f"正在构建索引... force={force}")
    print(f"  配置: embedding={store.embedding.model_name}, "
          f"bm25_k1={store.bm25_k1}, bm25_b={store.bm25_b}")
    count = store.build_index(force=force)
    print(f"索引构建完成，共 {count} 条记录。")


def cmd_stats(store: RAGStore, _args) -> None:
    stats = store.get_stats()
    print(f"Collection: {store.collection_name}")
    print(f"  总 chunk 数: {stats['total_chunks']}")
    print(f"  BM25 文档数: {stats['bm25_docs']}")
    print(f"  Embedding:   {stats['embedding_model']}")
    print(f"  涉及产品:    {', '.join(stats['products']) if stats['products'] else '(空)'}")


def cmd_search(store: RAGStore, args) -> None:
    mode = _get_mode(args)
    results = store.search(query=args.query, top_k=args.top_k, mode=mode)
    _print_results(results, args.by_product, mode)


def cmd_interactive(store: RAGStore, args) -> None:
    global _current_mode
    _current_mode = _get_mode(args)
    top_k = args.top_k

    stats = store.get_stats()
    if stats["total_chunks"] == 0:
        print("索引为空，请先执行 build 命令。")
        return

    print(f"交互检索模式（mode={_current_mode}, top_k={top_k}）")
    print("输入问题检索  |  :mode dense/sparse/hybrid 切换  |  :stats 统计  |  :q 退出\n")

    while True:
        try:
            query = input("🔍 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            break

        if not query:
            continue
        if query == ":q":
            print("已退出。")
            break
        if query == ":stats":
            cmd_stats(store, args)
            continue
        if query.startswith(":mode"):
            new_mode = query.replace(":mode", "").strip()
            if new_mode in ("dense", "sparse", "hybrid"):
                _current_mode = new_mode
                print(f"已切换为 {new_mode} 模式。\n")
            else:
                print(f"无效模式: {new_mode}，可选 dense/sparse/hybrid\n")
            continue

        results = store.search(query=query, top_k=top_k, mode=_current_mode)
        _print_results(results, False, _current_mode)


def _get_mode(args) -> str | None:
    return getattr(args, "mode", None) or None


def _print_results(results: list[dict], by_product: bool = False, mode: str | None = None) -> None:
    if not results:
        print("（无匹配结果）")
        return

    print(f"（检索模式: {mode or '—'}，共 {len(results)} 条）")

    if by_product:
        grouped: dict[str, list[dict]] = {}
        for r in results:
            product = r["metadata"].get("product", "未知产品")
            grouped.setdefault(product, []).append(r)
        for product, items in grouped.items():
            print(f"\n━━━ {product} ━━━")
            for item in items:
                _print_single_result(item)
    else:
        for item in results:
            _print_single_result(item)


def _print_single_result(item: dict) -> None:
    score = item["score"]
    bar = "█" * min(int(score * 10), 10)
    print(f"  [{bar:<10}] 分数: {score}")
    print(f"    来源: {item.get('source', '?')}")

    product = item["metadata"].get("product", "?")
    question = item["metadata"].get("question", "?")
    source_file = item["metadata"].get("source", "?")

    full_content = item.get("content", "")
    answer = ""
    if "\n回答: " in full_content:
        answer = full_content.split("\n回答: ", 1)[1]

    print(f"    产品: {product}")
    print(f"    问题: {question}")
    if answer:
        print(f"    回答: {answer}")
    print(f"    文件: {source_file}")
    print()


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="RAG 数据库 — CLI（临时，后续由 API 替代）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py build --force
  python main.py stats
  python main.py search "门锁没电了怎么办" --mode hybrid
  python main.py interactive
        """,
    )

    sub = parser.add_subparsers(dest="command", help="子命令")

    p_build = sub.add_parser("build", help="构建索引")
    p_build.add_argument("--force", action="store_true", help="强制重建")

    sub.add_parser("stats", help="查看统计")

    p_search = sub.add_parser("search", help="单次检索")
    p_search.add_argument("query", help="检索内容")
    p_search.add_argument("--top-k", type=int, help="返回结果数")
    p_search.add_argument("--mode", choices=["dense", "sparse", "hybrid"])
    p_search.add_argument("--by-product", action="store_true")

    p_inter = sub.add_parser("interactive", help="交互式检索")
    p_inter.add_argument("--top-k", type=int)
    p_inter.add_argument("--mode", choices=["dense", "sparse", "hybrid"])
    p_inter.add_argument("--by-product", action="store_true")

    args = parser.parse_args()

    store = RAGStore()
    store.build_index()

    if args.command == "build":
        cmd_build(store, args)
    elif args.command == "stats":
        cmd_stats(store, args)
    elif args.command == "search":
        cmd_search(store, args)
    elif args.command == "interactive":
        cmd_interactive(store, args)
    else:
        cmd_interactive(store, args)


if __name__ == "__main__":
    main()
