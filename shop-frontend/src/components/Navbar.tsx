import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import AuthModal from "./AuthModal";

export default function Navbar({
  cartCount,
  onOpenCart,
  onOpenOrders,
  onSearch,
}: {
  cartCount: number;
  onOpenCart: () => void;
  onOpenOrders: () => void;
  onSearch: (kw: string) => void;
}) {
  const { user, logout } = useAuth();
  const [showAuth, setShowAuth] = useState(false);
  const [kw, setKw] = useState("");

  return (
    <>
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center gap-6">
          <div className="text-xl font-bold text-blue-600 shrink-0">智居商城</div>

          <div className="flex-1 max-w-md">
            <input
              className="w-full px-4 py-2 bg-gray-100 rounded-full text-sm outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="搜索商品..."
              value={kw}
              onChange={(e) => setKw(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  onSearch(kw);
                  setKw("");
                }
              }}
            />
          </div>

          <div className="flex items-center gap-4 text-sm shrink-0">
            {user ? (
              <>
                <button onClick={onOpenOrders} className="text-gray-600 hover:text-blue-600">
                  我的订单
                </button>
                <button onClick={onOpenCart} className="relative text-gray-600 hover:text-blue-600">
                  🛒 购物车
                  {cartCount > 0 && (
                    <span className="absolute -top-2 -right-3 bg-red-500 text-white text-xs w-5 h-5 flex items-center justify-center rounded-full">
                      {cartCount}
                    </span>
                  )}
                </button>
                <span className="text-gray-400">|</span>
                <span className="text-gray-700">
                  {user.email.split("@")[0]}
                </span>
                <button onClick={logout} className="text-gray-400 hover:text-red-500">
                  退出
                </button>
              </>
            ) : (
              <button
                onClick={() => setShowAuth(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-full text-sm hover:bg-blue-700"
              >
                登录 / 注册
              </button>
            )}
          </div>
        </div>
      </nav>
      {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}
    </>
  );
}
