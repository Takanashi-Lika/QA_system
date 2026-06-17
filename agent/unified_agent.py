import os, json, logging
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

from agent.tools import create_shop_tools

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是智居商城（X-Home）的智能助手，你可以同时处理产品FAQ咨询和购物下单。

## 你可以做的事

### 产品FAQ（无需登录）
- 用户问产品怎么用、安装方法、故障排除、售后政策等 → 调用 search_faq 查找知识库
- 从返回结果中提取最相关的问答，用自然语言回复用户

### 购物下单（需登录）
- 搜索商品（search_products）
- 查看商品详情（get_product_detail）
- 加入购物车（add_to_cart）
- 查看购物车（view_cart）
- 创建订单（create_order）
- 支付订单（pay_order）
- 查看订单（list_orders）
- 查看个人信息（get_user_profile）

## 规则
- FAQ问题先搜索知识库，不要编造答案
- 购物相关先去 search_products 找到商品
- 未登录时调用购物工具会失败，告诉用户先去首页登录
- 回复简洁自然，像真人客服
- 任何不确定的操作，先调用工具确认后再回复用户"""


class UnifiedAgent:
    def __init__(self, user_token: str = ""):
        self._user_token = user_token
        self._pipeline = None
        self._init_tools()
        self._init_llm()

    def _init_tools(self):
        shop_tools = create_shop_tools(self._user_token) if self._user_token else []
        all_tools = [self._make_faq_tool()] + shop_tools
        self._tools = all_tools
        self._tool_map = {t.name: t for t in self._tools}

    def _make_faq_tool(self) -> StructuredTool:
        def search_faq(question: str) -> str:
            """搜索产品FAQ知识库：用于回答产品使用、安装、故障、售后政策等问题。传入用户的具体问题，返回最相关的FAQ问答对。"""
            if self._pipeline is None:
                from retriever import RetrieverPipeline
                self._pipeline = RetrieverPipeline()
            results = self._pipeline.search(question, top_k=3)
            if not results:
                return "知识库中暂无相关内容。"
            parts = []
            for i, r in enumerate(results, 1):
                product = r["metadata"].get("product", "")
                q = r["metadata"].get("question", "")
                a = ""
                content = r.get("content", "")
                if "\n回答: " in content:
                    a = content.split("\n回答: ", 1)[1]
                parts.append(f"{i}.【{product}】问：{q}\n   答：{a}")
            return "\n\n".join(parts)

        return StructuredTool.from_function(func=search_faq)

    def _init_llm(self):
        self._llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "deepseek-chat"),
            openai_api_key=os.getenv("MODEL_API_KEY", ""),
            openai_api_base=os.getenv("MODEL_BASE_URL", "https://api.deepseek.com/v1"),
            temperature=0.1,
        )
        if self._tools:
            self._llm = self._llm.bind_tools(self._tools)

    def chat(self, messages: list[dict]) -> dict:
        langchain_msgs = [SystemMessage(content=SYSTEM_PROMPT)]
        for m in messages:
            if m["role"] == "user":
                langchain_msgs.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                langchain_msgs.append(AIMessage(content=m.get("content", "")))

        tool_calls_log: list[dict] = []

        for _ in range(5):
            response = self._llm.invoke(langchain_msgs)

            if not response.tool_calls:
                return {"response": response.content or "", "tool_calls": tool_calls_log}

            langchain_msgs.append(response)
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_func = self._tool_map.get(tool_name)

                if tool_func:
                    try:
                        result = tool_func.invoke(tool_args)
                    except Exception as e:
                        result = f"工具调用失败: {e}"
                else:
                    result = f"未知工具: {tool_name}"

                tool_calls_log.append({"name": tool_name, "args": tool_args, "result": str(result)[:500]})
                langchain_msgs.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

        return {"response": "抱歉，操作步骤过多，请简化后再试。", "tool_calls": tool_calls_log}
