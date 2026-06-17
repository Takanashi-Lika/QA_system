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

const TABS: { key: Tab; icon: string; label: string }[] = [
  { key: "home", icon: "🏠", label: "首页" },
  { key: "orders", icon: "📋", label: "我的订单" },
  { key: "ai", icon: "🤖", label: "AI助手" },
];

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
    if (qty <= 0) await api.removeFromCart(productId);
    else await api.updateCartItem(productId, qty);
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

  const search = (kw: string) => {
    setTab("home");
  };

  return (
    <div className="min-h-screen">
      <Navbar cartCount={cartItems.length} onOpenCart={() => setCartOpen(true)} onOpenOrders={() => setTab("orders")} onSearch={search} />

      <div className="max-w-7xl mx-auto px-6 pt-4 pb-20">
        <div className="flex items-center gap-1 mb-6 bg-white/60 backdrop-blur rounded-2xl p-1.5 w-fit border border-gray-50 shadow-sm">
          {TABS.map((t) => (
            <button
              key={t.key}
              className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
                tab === t.key
                  ? "bg-gradient-to-r from-[#1a1a2e] to-[#e94560] text-white shadow-md"
                  : "text-gray-500 hover:text-[#1a1a2e] hover:bg-gray-50"
              }`}
              onClick={() => setTab(t.key)}
            >
              <span className="mr-1.5">{t.icon}</span>{t.label}
            </button>
          ))}
        </div>

        {tab === "home" && <HomeTab onDetail={(p) => setDetailProduct(p)} onAddCart={addToCart} />}
        {tab === "orders" && <OrdersTab />}
        {tab === "ai" && <AiChatTab />}
      </div>

      <CartDrawer open={cartOpen} items={cartItems} total={cartTotal} onClose={() => setCartOpen(false)} onUpdateQty={updateQty} onRemove={removeFromCart} onCheckout={checkout} />
      {detailProduct && <ProductDetail product={detailProduct} cartItems={cartItems} onClose={() => setDetailProduct(null)} onAddCart={addToCart} onUpdateQty={updateQty} />}

      <footer className="text-center py-8 text-xs text-gray-400">
        © 2026 智居商城 — 基于 FastAPI + React + PostgreSQL + Redis + RAG 智能客服 · 演示项目
      </footer>
    </div>
  );
}
