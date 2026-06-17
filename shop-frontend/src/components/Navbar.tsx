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
      <nav className="sticky top-0 z-40 backdrop-blur-xl bg-white/80 border-b border-gray-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center gap-6">
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#1a1a2e] to-[#e94560] flex items-center justify-center text-white text-sm font-extrabold">
              ZH
            </div>
            <span className="text-lg font-extrabold bg-gradient-to-r from-[#1a1a2e] to-[#e94560] bg-clip-text text-transparent tracking-tight">
              智居商城
            </span>
          </div>

          <div className="flex-1 max-w-lg">
            <div className="relative">
              <svg className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-100 rounded-2xl text-sm outline-none focus:bg-white focus:border-[#1a1a2e]/20 focus:ring-4 focus:ring-[#1a1a2e]/5 transition-all duration-200 placeholder:text-gray-400"
                placeholder="搜索商品..."
                value={kw}
                onChange={(e) => setKw(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") { onSearch(kw); setKw(""); }
                }}
              />
            </div>
          </div>

          <div className="flex items-center gap-1 text-sm shrink-0">
            {user ? (
              <>
                <button onClick={onOpenOrders} className="px-3.5 py-2 rounded-xl text-gray-600 hover:text-[#1a1a2e] hover:bg-gray-50 transition-all duration-200 font-medium">
                  我的订单
                </button>
                <button onClick={onOpenCart} className="relative px-3.5 py-2 rounded-xl text-gray-600 hover:text-[#1a1a2e] hover:bg-gray-50 transition-all duration-200 font-medium">
                  <svg className="w-5 h-5 inline mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" />
                  </svg>
                  购物车
                  {cartCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-[#e94560] text-white text-[10px] min-w-[18px] h-[18px] flex items-center justify-center rounded-full font-bold animate-scale-in px-1">
                      {cartCount}
                    </span>
                  )}
                </button>
                <span className="w-px h-5 bg-gray-200 mx-1" />
                <div className="flex items-center gap-2 px-2 py-1.5 rounded-xl bg-gray-50">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#1a1a2e] to-[#e94560] flex items-center justify-center text-white text-[10px] font-bold">
                    {user.email.charAt(0).toUpperCase()}
                  </div>
                  <span className="text-gray-700 font-medium text-xs">{user.email.split("@")[0]}</span>
                </div>
                <button onClick={logout} className="ml-1 px-3 py-2 rounded-xl text-gray-400 hover:text-[#e94560] hover:bg-red-50 transition-all duration-200 text-xs">
                  退出
                </button>
              </>
            ) : (
              <button
                onClick={() => setShowAuth(true)}
                className="px-5 py-2.5 bg-gradient-to-r from-[#1a1a2e] to-[#e94560] text-white rounded-2xl text-sm font-semibold hover:shadow-lg hover:shadow-[#e94560]/20 transition-all duration-300 active:scale-95"
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
