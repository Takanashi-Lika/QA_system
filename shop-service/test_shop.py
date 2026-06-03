import sys, os, json
import httpx

BASE_URL = os.getenv("SHOP_URL", "http://localhost:8001")


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        print(f"FAIL [{msg}]: expected={expected}, actual={actual}")
        sys.exit(1)


def assert_status(resp, expected_code, msg=""):
    assert_eq(resp.status_code, expected_code, f"{msg} status_code")


def assert_code(resp, expected_biz_code, msg=""):
    data = resp.json()
    assert_eq(data.get("code"), expected_biz_code, f"{msg} biz_code")


def test_health():
    print("0. 健康检查...")
    resp = httpx.get(f"{BASE_URL}/health")
    assert_status(resp, 200, "health")
    assert resp.json()["status"] == "ok"
    print("   通过 ✓")


def test_auth():
    print("1. 用户注册...")
    resp = httpx.post(f"{BASE_URL}/c-endpoint/register", json={
        "email": "test@test.com", "password": "123456", "nickname": "测试用户"
    })
    assert_status(resp, 200, "register")
    assert_code(resp, 0, "register")

    print("   重复注册...")
    resp = httpx.post(f"{BASE_URL}/c-endpoint/register", json={
        "email": "test@test.com", "password": "123456", "nickname": "测试用户2"
    })
    assert_status(resp, 400, "duplicate register")
    assert_code(resp, 40001, "duplicate register")

    print("2. 用户登录...")
    resp = httpx.post(f"{BASE_URL}/c-endpoint/login", json={
        "email": "test@test.com", "password": "123456"
    })
    assert_status(resp, 200, "login")
    assert_code(resp, 0, "login")
    token = resp.json()["data"]["token"]
    print(f"   Token: {token[:20]}...")
    assert token is not None and len(token) > 0

    print("   错误密码登录...")
    resp = httpx.post(f"{BASE_URL}/c-endpoint/login", json={
        "email": "test@test.com", "password": "wrongpass"
    })
    assert_status(resp, 401, "wrong password")
    assert_code(resp, 40101, "wrong password")

    return token


def test_user_profile(token):
    print("3. 个人信息...")
    headers = {"Authorization": f"Bearer {token}"}

    resp = httpx.get(f"{BASE_URL}/c-endpoint/me", headers=headers)
    assert_status(resp, 200, "get profile")
    assert resp.json()["data"]["email"] == "test@test.com"

    print("   更新地址...")
    resp = httpx.put(f"{BASE_URL}/c-endpoint/address", json={"address": "广东省深圳市南山区"}, headers=headers)
    assert_status(resp, 200, "update address")
    assert resp.json()["data"]["address"] == "广东省深圳市南山区"
    print("   通过 ✓")


def test_products():
    print("4. 商品浏览...")

    print("   分类树...")
    resp = httpx.get(f"{BASE_URL}/b-endpoint/categories/")
    assert_status(resp, 200, "categories")
    data = resp.json()["data"]
    assert len(data) > 0, "categories should not be empty"
    print(f"   共 {len(data)} 个一级分类")

    print("   热门商品...")
    resp = httpx.get(f"{BASE_URL}/c-endpoint/products/hot")
    assert_status(resp, 200, "hot products")
    hot_data = resp.json()["data"]
    print(f"   热门商品: {len(hot_data)} 条")

    print("   商品列表...")
    resp = httpx.get(f"{BASE_URL}/c-endpoint/products")
    assert_status(resp, 200, "product list")
    items = resp.json()["data"].get("items", [])
    print(f"   商品列表: {len(items)} 条")
    product_id = items[0]["id"] if items else 1

    print("   搜索...")
    resp = httpx.get(f"{BASE_URL}/c-endpoint/products?keyword=门锁")
    assert_status(resp, 200, "search")

    print("   商品详情...")
    resp = httpx.get(f"{BASE_URL}/c-endpoint/products/{product_id}")
    assert_status(resp, 200, "product detail")
    assert resp.json()["data"]["id"] == product_id

    print("   不存在商品...")
    resp = httpx.get(f"{BASE_URL}/c-endpoint/products/99999")
    assert_status(resp, 404, "product 404")
    print("   通过 ✓")
    return product_id


def test_cart(token, product_id):
    print("5. 购物车...")
    headers = {"Authorization": f"Bearer {token}"}

    print("   添加商品...")
    resp = httpx.post(f"{BASE_URL}/c-endpoint/cart/", json={"product_id": product_id, "quantity": 2}, headers=headers)
    assert_status(resp, 200, "add cart")
    assert_code(resp, 0, "add cart")

    print("   重复添加（UPSERT）...")
    resp = httpx.post(f"{BASE_URL}/c-endpoint/cart/", json={"product_id": product_id, "quantity": 3}, headers=headers)
    assert_status(resp, 200, "upsert cart")
    assert_code(resp, 0, "upsert cart")

    print("   查看购物车...")
    resp = httpx.get(f"{BASE_URL}/c-endpoint/cart/", headers=headers)
    assert_status(resp, 200, "view cart")
    cart_data = resp.json()["data"]
    print(f"   商品数: {len(cart_data['items'])}, 总金额: {cart_data['total_amount']}")

    print("   修改数量...")
    resp = httpx.put(f"{BASE_URL}/c-endpoint/cart/{product_id}", json={"quantity": 1}, headers=headers)
    assert_status(resp, 200, "update cart")
    print("   通过 ✓")


def test_order(token):
    print("6. 订单创建...")
    headers = {"Authorization": f"Bearer {token}"}

    resp = httpx.post(f"{BASE_URL}/c-endpoint/orders/", json={"address": "广东省深圳市南山区"}, headers=headers)
    assert_status(resp, 200, "create order")
    assert_code(resp, 0, "create order")
    order_id = resp.json()["data"]["id"]
    print(f"   订单ID: {order_id}")

    print("7. 订单支付...")
    resp = httpx.post(f"{BASE_URL}/c-endpoint/orders/{order_id}/pay", headers=headers)
    assert_status(resp, 200, "pay order")
    assert_code(resp, 0, "pay order")
    print(f"   状态: {resp.json()['data']['status']}")

    print("   重复支付...")
    resp = httpx.post(f"{BASE_URL}/c-endpoint/orders/{order_id}/pay", headers=headers)
    assert_status(resp, 422, "duplicate pay")
    assert_code(resp, 42201, "duplicate pay")

    print("8. 订单查询...")
    resp = httpx.get(f"{BASE_URL}/c-endpoint/orders/", headers=headers)
    assert_status(resp, 200, "order list")
    assert_code(resp, 0, "order list")
    print(f"   订单数: {resp.json()['data']['total']}")

    resp = httpx.get(f"{BASE_URL}/c-endpoint/orders/{order_id}", headers=headers)
    assert_status(resp, 200, "order detail")
    assert_code(resp, 0, "order detail")
    print(f"   明细数: {len(resp.json()['data']['items'])}")

    return order_id


def test_logistics(token, order_id):
    print("9. 物流追踪...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.get(f"{BASE_URL}/c-endpoint/logistics?order_id={order_id}", headers=headers)
    assert_status(resp, 200, "logistics")
    assert_code(resp, 0, "logistics")
    log_data = resp.json()["data"]
    print(f"   物流状态: {log_data.get('status', 'N/A')}")
    print("   通过 ✓")


def test_after_sale(token, order_id):
    print("10. 售后申请...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.post(f"{BASE_URL}/c-endpoint/after-sales", json={
        "order_id": order_id, "type": "refund", "reason": "不想要了"
    }, headers=headers)
    assert_status(resp, 200, "after sale")
    assert_code(resp, 0, "after sale")

    print("   查看售后...")
    resp = httpx.get(f"{BASE_URL}/c-endpoint/after-sales", headers=headers)
    assert_status(resp, 200, "view after sales")
    assert_code(resp, 0, "view after sales")
    print("   通过 ✓")


def test_cancel_order(token):
    print("11. 取消订单...")
    headers = {"Authorization": f"Bearer {token}"}

    resp = httpx.post(f"{BASE_URL}/c-endpoint/orders/", json={"address": "北京市朝阳区"}, headers=headers)
    assert_status(resp, 200, "create for cancel")
    cancel_order_id = resp.json()["data"]["id"]

    resp = httpx.delete(f"{BASE_URL}/c-endpoint/orders/{cancel_order_id}", headers=headers)
    assert_status(resp, 200, "cancel")
    assert_code(resp, 0, "cancel")
    assert resp.json()["data"]["status"] == "cancelled"

    print("   已取消的订单不可支付...")
    resp = httpx.post(f"{BASE_URL}/c-endpoint/orders/{cancel_order_id}/pay", headers=headers)
    assert_status(resp, 422, "cancelled pay")
    print("   通过 ✓")


def test_admin():
    print("12. 管理员功能...")

    admin_email = "admin@shop.local"
    admin_password = "admin123"

    resp = httpx.post(f"{BASE_URL}/c-endpoint/login", json={
        "email": admin_email, "password": admin_password
    })
    assert_status(resp, 200, "admin login")
    admin_token = resp.json()["data"]["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    print("   查看全部订单...")
    resp = httpx.get(f"{BASE_URL}/b-endpoint/orders/", headers=admin_headers)
    assert_status(resp, 200, "admin orders")
    assert_code(resp, 0, "admin orders")

    print("   创建分类...")
    resp = httpx.post(f"{BASE_URL}/b-endpoint/categories/", json={"name": "测试分类"}, headers=admin_headers)
    assert_status(resp, 200, "create category")
    cat_id = resp.json()["data"]["id"]

    print("   发布商品...")
    resp = httpx.post(f"{BASE_URL}/b-endpoint/products/", json={
        "name": "测试商品", "description": "测试", "price": 99.9, "stock": 50, "category_id": cat_id
    }, headers=admin_headers)
    assert_status(resp, 200, "create product")
    prod_id = resp.json()["data"]["id"]

    print("   编辑商品...")
    resp = httpx.put(f"{BASE_URL}/b-endpoint/products/{prod_id}", json={"name": "测试商品(已编辑)"}, headers=admin_headers)
    assert_status(resp, 200, "edit product")
    assert resp.json()["data"]["name"] == "测试商品(已编辑)"

    print("   下架商品...")
    resp = httpx.patch(f"{BASE_URL}/b-endpoint/products/{prod_id}/status", headers=admin_headers)
    assert_status(resp, 200, "toggle status")
    print("   通过 ✓")
    return admin_headers


def test_permission(token):
    print("13. 权限隔离...")
    user_headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.get(f"{BASE_URL}/b-endpoint/orders/", headers=user_headers)
    assert_status(resp, 403, "user to b-end")
    assert_code(resp, 40301, "user to b-end")
    print("   通过 ✓")


def main():
    print("=" * 60)
    print("电商平台 Shop-Service 端到端测试")
    print("=" * 60)

    test_health()
    token = test_auth()
    test_user_profile(token)

    product_id = test_products()
    test_cart(token, product_id)
    order_id = test_order(token)
    test_logistics(token, order_id)
    test_after_sale(token, order_id)
    test_cancel_order(token)
    test_admin()
    test_permission(token)

    print("\n" + "=" * 60)
    print("全部测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    main()
