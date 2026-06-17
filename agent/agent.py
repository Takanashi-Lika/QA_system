import os
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

from agent.tools import create_shop_tools

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是智居商城的智能购物助手，可以帮助用户通过自然语言浏览和购买商品。

你可以使用工具完成以下操作：
- 搜索商品（search_products）
- 查看商品详情（get_product_detail）
- 加入购物车（add_to_cart）
- 查看购物车（view_cart）
- 创建订单（create_order）
- 支付订单（pay_order）
- 查看订单（list_orders）
- 查看个人信息（get_user_profile）

工作流程：
1. 用户说想买什么东西 → 先用 search_products 搜索
2. 找到商品后告知用户，如果有多款让用户选择
3. 用户确认后 → 调用 add_to_cart 加购 → 再调用 create_order 下单
4. 下单前如果没有地址 → 先调用 get_user_profile 获取默认地址
5. 下单成功后 → 告知用户订单号和金额

注意事项：
- 用户说"第一个""第二个"时，根据之前搜索结果中的顺序选择
- 用户指定数量时传递对应 quantity 参数
- 每次回复尽量简洁友好，不要长篇大论
- 涉及付款、价格时必须准确引用工具返回的金额"""


class ShoppingAgent:
    def __init__(self, user_token: str):
        self._tools = create_shop_tools(user_token)
        self._tool_map = {t.name: t for t in self._tools}

        self._llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "deepseek-chat"),
            openai_api_key=os.getenv("MODEL_API_KEY", ""),
            openai_api_base=os.getenv("MODEL_BASE_URL", "https://api.deepseek.com/v1"),
            temperature=0.1,
        ).bind_tools(self._tools)

    def chat(self, messages: list[dict]) -> dict:
        """处理一轮对话，可能包含多次工具调用。

        messages 格式: [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}]
        返回: {"response": "助手回复文本", "tool_calls": [{"name":"...","result":"..."}]}
        """
        langchain_msgs = [SystemMessage(content=SYSTEM_PROMPT)]
        for m in messages:
            if m["role"] == "user":
                langchain_msgs.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                langchain_msgs.append(AIMessage(content=m.get("content", "")))

        tool_calls_log: list[dict] = []

        # 最多 5 轮工具调用防止死循环
        for _ in range(5):
            response = self._llm.invoke(langchain_msgs)

            if not response.tool_calls:
                return {"response": response.content or "", "tool_calls": tool_calls_log}

            # 执行所有工具调用
            langchain_msgs.append(response)
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_func = self._tool_map.get(tool_name)

                if tool_func:
                    try:
                        result = tool_func.invoke(tool_args)
                    except Exception as e:
                        result = f"工具执行异常: {e}"
                else:
                    result = f"未知工具: {tool_name}"

                tool_calls_log.append({"name": tool_name, "args": tool_args, "result": result})
                langchain_msgs.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

        return {"response": "抱歉，操作步骤过多，请简化您的需求后再试。", "tool_calls": tool_calls_log}
