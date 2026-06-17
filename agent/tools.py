import os, json, httpx
from langchain_core.tools import StructuredTool

SHOP_BASE = os.getenv("SHOP_SERVICE_URL", "http://localhost:8001")


def _headers(user_token: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user_token}",
    }


def _safe(r: httpx.Response) -> str:
    try:
        body = r.json()
        if r.status_code >= 400:
            return f"❌ 错误: {body.get('message', r.text)}"
        return json.dumps(body.get("data", body), ensure_ascii=False, indent=2)
    except Exception:
        return r.text


def create_shop_tools(user_token: str) -> list[StructuredTool]:
    """为指定用户创建工具集，user_token 闭包注入，LLM 无感知。"""

    def search_products(keyword: str) -> str:
        """搜索商品：输入中文关键词（如"门锁""摄像头"），返回匹配商品的名称、价格、库存、ID。用户想买东西时先调用此工具找到商品。"""
        r = httpx.get(f"{SHOP_BASE}/c-endpoint/products", params={"keyword": keyword})
        return _safe(r)

    def get_product_detail(product_id: int) -> str:
        """查询单个商品详情：传入商品ID，返回名称、价格、库存、描述。"""
        r = httpx.get(f"{SHOP_BASE}/c-endpoint/products/{product_id}")
        return _safe(r)

    def add_to_cart(product_id: int, quantity: int = 1) -> str:
        """把商品加入购物车：传入 product_id 和 quantity（默认1）。"""
        r = httpx.post(
            f"{SHOP_BASE}/c-endpoint/cart/",
            json={"product_id": product_id, "quantity": quantity},
            headers=_headers(user_token),
        )
        return _safe(r)

    def view_cart() -> str:
        """查看当前用户的购物车：返回商品列表和合计金额。"""
        r = httpx.get(f"{SHOP_BASE}/c-endpoint/cart/", headers=_headers(user_token))
        return _safe(r)

    def create_order(address: str) -> str:
        """从购物车创建订单：传入收货地址。购物车不能为空，创建后购物车自动清空。"""
        r = httpx.post(
            f"{SHOP_BASE}/c-endpoint/orders/",
            json={"address": address},
            headers=_headers(user_token),
        )
        return _safe(r)

    def pay_order(order_id: int) -> str:
        """支付订单：传入 order_id。只能支付待支付状态的订单，已支付/已取消的订单会报错。"""
        r = httpx.post(
            f"{SHOP_BASE}/c-endpoint/orders/{order_id}/pay",
            headers=_headers(user_token),
        )
        return _safe(r)

    def list_orders() -> str:
        """查看所有订单：返回订单ID、金额、状态、时间。"""
        r = httpx.get(f"{SHOP_BASE}/c-endpoint/orders/", headers=_headers(user_token))
        return _safe(r)

    def get_user_profile() -> str:
        """获取个人信息：返回昵称、邮箱、收货地址。下单前应先调用此工具获取默认地址。"""
        r = httpx.get(f"{SHOP_BASE}/c-endpoint/me", headers=_headers(user_token))
        return _safe(r)

    return [
        StructuredTool.from_function(func=search_products),
        StructuredTool.from_function(func=get_product_detail),
        StructuredTool.from_function(func=add_to_cart),
        StructuredTool.from_function(func=view_cart),
        StructuredTool.from_function(func=create_order),
        StructuredTool.from_function(func=pay_order),
        StructuredTool.from_function(func=list_orders),
        StructuredTool.from_function(func=get_user_profile),
    ]
