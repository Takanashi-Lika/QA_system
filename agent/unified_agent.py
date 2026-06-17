import os, json, logging, httpx
from openai import OpenAI
from retriever import RetrieverPipeline

logger = logging.getLogger(__name__)

SHOP_BASE = os.getenv("SHOP_SERVICE_URL", "http://localhost:8001")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_faq",
            "description": "搜索产品FAQ知识库。用于回答产品使用、安装、故障、售后政策等问题。传入用户问题字符串，返回最相关的FAQ问答对。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "用户的原始问题"}
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "搜索商品：传入中文关键词（如'门锁''摄像头'），返回匹配商品的名称、价格、库存、ID。用户想买东西时先调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_detail",
            "description": "查询单个商品详情。传入商品ID，返回名称、价格、库存、描述。",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "商品ID"}
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "把商品加入购物车。传入 product_id 和 quantity（默认1）。需要用户已登录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "商品ID"},
                    "quantity": {"type": "integer", "description": "数量，默认1", "default": 1},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_cart",
            "description": "查看当前用户的购物车内容，返回商品列表和合计金额。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_order",
            "description": "从购物车创建订单。传入收货地址。购物车不能为空，创建后购物车自动清空。",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {"type": "string", "description": "收货地址"}
                },
                "required": ["address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pay_order",
            "description": "支付订单。传入 order_id。只能支付待支付状态的订单。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "订单ID"}
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_orders",
            "description": "查看所有订单，返回订单ID、金额、状态、时间。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "获取用户个人信息（昵称、邮箱、收货地址）。下单前应先调用此工具获取默认地址。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

SYSTEM_PROMPT = """你是智居商城（X-Home）的智能助手，可以同时处理产品FAQ咨询和购物下单。

规则：
- 产品使用/安装/故障/售后问题 → 调用 search_faq 查知识库，不要编造
- 购物需求 → 先 search_products 找商品 → 再 add_to_cart → 再 create_order
- 未登录时购物工具会失败，告诉用户先去首页登录
- 回复简洁自然，像真人客服
- 不确定时先调工具确认再回用户"""


class UnifiedAgent:
    def __init__(self, user_token: str = ""):
        self._user_token = user_token
        self._client = OpenAI(
            api_key=os.getenv("MODEL_API_KEY", ""),
            base_url=os.getenv("MODEL_BASE_URL", "https://api.deepseek.com/v1"),
            timeout=float(os.getenv("MODEL_TIMEOUT", "120")),
            http_client=httpx.Client(proxy=None),
        )
        self._model = os.getenv("MODEL_NAME", "deepseek-chat")
        self._pipeline = None

    def _shop_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._user_token}",
        }

    def _safe(self, r: httpx.Response) -> str:
        try:
            body = r.json()
            if r.status_code >= 400:
                return f"错误: {body.get('message', r.text)}"
            return json.dumps(body.get("data", body), ensure_ascii=False, indent=2)
        except Exception:
            return r.text

    def _execute_tool(self, name: str, args: dict) -> str:
        if name == "search_faq":
            if self._pipeline is None:
                self._pipeline = RetrieverPipeline()
            results = self._pipeline.search(args["question"], top_k=3)
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

        elif name == "search_products":
            r = httpx.get(f"{SHOP_BASE}/c-endpoint/products", params={"keyword": args["keyword"]})
            return self._safe(r)

        elif name == "get_product_detail":
            r = httpx.get(f"{SHOP_BASE}/c-endpoint/products/{args['product_id']}")
            return self._safe(r)

        elif name == "add_to_cart":
            r = httpx.post(f"{SHOP_BASE}/c-endpoint/cart/", json={
                "product_id": args["product_id"],
                "quantity": args.get("quantity", 1),
            }, headers=self._shop_headers())
            return self._safe(r)

        elif name == "view_cart":
            r = httpx.get(f"{SHOP_BASE}/c-endpoint/cart/", headers=self._shop_headers())
            return self._safe(r)

        elif name == "create_order":
            r = httpx.post(f"{SHOP_BASE}/c-endpoint/orders/", json={
                "address": args["address"],
            }, headers=self._shop_headers())
            return self._safe(r)

        elif name == "pay_order":
            r = httpx.post(f"{SHOP_BASE}/c-endpoint/orders/{args['order_id']}/pay",
                           headers=self._shop_headers())
            return self._safe(r)

        elif name == "list_orders":
            r = httpx.get(f"{SHOP_BASE}/c-endpoint/orders/", headers=self._shop_headers())
            return self._safe(r)

        elif name == "get_user_profile":
            r = httpx.get(f"{SHOP_BASE}/c-endpoint/me", headers=self._shop_headers())
            return self._safe(r)

        return f"未知工具: {name}"

    def chat(self, messages: list[dict]) -> dict:
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in messages:
            msgs.append({
                "role": m["role"],
                "content": m.get("content", ""),
            })

        tool_calls_log = []

        for _ in range(5):
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=msgs,
                tools=TOOLS,
                temperature=0.1,
            )
            choice = resp.choices[0]

            if not choice.message.tool_calls:
                return {"response": choice.message.content or "", "tool_calls": tool_calls_log}

            msgs.append(choice.message)

            for tc in choice.message.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                result = self._execute_tool(name, args)
                tool_calls_log.append({"name": name, "args": args, "result": str(result)[:500]})
                msgs.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result),
                })

        return {"response": "抱歉，操作步骤过多，请简化后再试。", "tool_calls": tool_calls_log}
