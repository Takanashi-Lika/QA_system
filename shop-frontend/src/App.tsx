import { useEffect, useState, useCallback } from "react";
import { api } from "./api";
import { useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import CartDrawer from "./components/CartDrawer";
import ProductDetail from "./components/ProductDetail";
import HomeTab from "./pages/HomeTab";
import OrdersTab from "./pages/OrdersTab";
import AiChatTab from "./pages/AiChatTab";

interface Product {
  id: number;
  name: string;
  price: number;
  stock: number;
  description?: string;
}

interface CartItem {
  product_id: number;
  product_name: string;
  price: number;
  quantity: number;
  stock: number;
}

type Tab = "home" | "orders" | "ai";

export default function App() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("home");
  const [cartOpen, setCartOpen] = useState(false);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [cartTotal, setCartTotal] = useState(0);
  const [detailProduct, setDetailProduct] = useState<Product | null>(null);

  const loadCart = useCallback(async () => {
    if (!user) return;
    const r = await api.getCart();
    if (r.code === 0) {
      setCartItems(r.data?.items || []);
      setCartTotal(r.data?.total_amount || 0);
    }
  }, [user]);

  useEffect(() => { loadCart(); }, [loadCart]);

  const addToCart = async (p: Product) => {
    if (!user) { alert("请先登录"); return; }
    await api.addToCart(p.id, 1);
    loadCart();
    setDetailProduct(null);
  };

  const updateQty = async (productId: number, qty: number) => {
    if (qty <= 0) {
      await api.removeFromCart(productId);
    } else {
      await api.updateCartItem(productId, qty);
    }
    loadCart();
  };

  const removeFromCart = async (productId: number) => {
    await api.removeFromCart(productId);
    loadCart();
  };

  const checkout = async (address: string) => {
    const r = await api.createOrder(address);
    if (r.code === 0) {
      await api.payOrder(r.data.id);
      alert(`下单成功！订单号 #${r.data.id}，已自动支付`);
      setCartOpen(false);
      setCartItems([]);
      setCartTotal(0);
      setTab("orders");
    } else {
      alert(r.message || "下单失败");
    }
  };

  const search = async (kw: string) => {
    setTab("home");
    const r = await api.getProducts({ keyword: kw });
    if (r.code === 0) {
      const items = Array.isArray(r.data) ? r.data : (r.data?.items || []);
      setDetailProduct(items[0] || null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar
        cartCount={cartItems.length}
        onOpenCart={() => setCartOpen(true)}
        onOpenOrders={() => setTab("orders")}
        onSearch={search}
      />

      <div className="flex border-b bg-white">
        {(["home", "orders", "ai"] as Tab[]).map((t) => (
          <button
            key={t}
            className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? "border-blue-600 text-blue-600" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => setTab(t)}
          >
            {{ home: "🏠 首页", orders: "📋 我的订单", ai: "🤖 AI客服" }[t]}
          </button>
        ))}
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {tab === "home" && (
          <HomeTab onDetail={(p) => setDetailProduct(p)} onAddCart={addToCart} />
        )}
        {tab === "orders" && <OrdersTab />}
        {tab === "ai" && <AiChatTab />}
      </div>

      <CartDrawer
        open={cartOpen}
        items={cartItems}
        total={cartTotal}
        onClose={() => setCartOpen(false)}
        onUpdateQty={updateQty}
        onRemove={removeFromCart}
        onCheckout={checkout}
      />

      {detailProduct && (
        <ProductDetail
          product={detailProduct}
          cartItems={cartItems}
          onClose={() => setDetailProduct(null)}
          onAddCart={addToCart}
          onUpdateQty={updateQty}
        />
      )}
    </div>
  );
}
