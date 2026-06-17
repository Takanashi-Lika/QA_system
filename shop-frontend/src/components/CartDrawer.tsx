import { useState } from "react";
import { useAuth } from "../context/AuthContext";

interface CartItem {
  product_id: number;
  product_name: string;
  price: number;
  quantity: number;
  stock: number;
}

export default function CartDrawer({
  open,
  items,
  total,
  onClose,
  onUpdateQty,
  onRemove,
  onCheckout,
}: {
  open: boolean;
  items: CartItem[];
  total: number;
  onClose: () => void;
  onUpdateQty: (productId: number, qty: number) => void;
  onRemove: (productId: number) => void;
  onCheckout: (address: string) => void;
}) {
  const { user } = useAuth();
  const [address, setAddress] = useState("广东省深圳市南山区");
  const [showCheckout, setShowCheckout] = useState(false);

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex justify-end" onClick={onClose}>
      <div className="w-[440px] bg-white h-full shadow-2xl flex flex-col animate-slide-in-right" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-50">
          <div>
            <h3 className="text-lg font-extrabold text-[#1a1a2e]">购物车</h3>
            <p className="text-xs text-gray-400 mt-0.5">{items.length} 件商品</p>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-full bg-gray-50 flex items-center justify-center text-gray-400 hover:text-[#1a1a2e] hover:bg-gray-100 transition-all text-lg">&times;</button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {items.length === 0 ? (
            <div className="text-center py-20">
              <div className="text-5xl mb-4 opacity-30">🛒</div>
              <p className="text-gray-400">购物车是空的</p>
            </div>
          ) : (
            items.map((item) => (
              <div key={item.product_id} className="flex items-center gap-4 py-4 border-b border-gray-50">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-50 to-rose-50 flex items-center justify-center text-2xl shrink-0">📦</div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm text-[#1a1a2e] truncate">{item.product_name}</p>
                  <p className="text-[#e94560] font-bold text-sm">¥{item.price}</p>
                </div>
                <div className="flex items-center gap-1.5">
                  <button className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-sm text-gray-500 hover:border-[#1a1a2e] hover:text-[#1a1a2e] transition-all" onClick={() => onUpdateQty(item.product_id, item.quantity - 1)}>-</button>
                  <span className="w-6 text-center font-bold text-sm">{item.quantity}</span>
                  <button className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-sm text-gray-500 hover:border-[#1a1a2e] hover:text-[#1a1a2e] transition-all" onClick={() => onUpdateQty(item.product_id, item.quantity + 1)}>+</button>
                </div>
                <button className="text-xs text-gray-400 hover:text-[#e94560] transition-colors ml-1" onClick={() => onRemove(item.product_id)}>删除</button>
              </div>
            ))
          )}
        </div>

        {items.length > 0 && (
          <div className="px-6 py-5 border-t border-gray-50 bg-gray-50/50">
            <div className="flex justify-between items-end mb-4">
              <span className="text-sm text-gray-500">合计</span>
              <div>
                <span className="text-xs text-gray-400">¥</span>
                <span className="text-3xl font-extrabold text-[#1a1a2e]">{total}</span>
              </div>
            </div>
            {!showCheckout ? (
              <button onClick={() => { if (!user) { alert("请先登录"); return; } setShowCheckout(true); }} className="w-full py-3.5 bg-gradient-to-r from-[#1a1a2e] to-[#e94560] text-white rounded-2xl font-bold text-sm hover:shadow-lg hover:shadow-[#e94560]/25 transition-all duration-300 active:scale-[0.98]">
                去结算
              </button>
            ) : (
              <div className="space-y-3">
                <input className="w-full px-4 py-3 bg-white border border-gray-100 rounded-2xl text-sm outline-none focus:border-[#1a1a2e]/20 focus:ring-4 focus:ring-[#1a1a2e]/5 transition-all" placeholder="收货地址" value={address} onChange={(e) => setAddress(e.target.value)} />
                <button onClick={() => onCheckout(address)} className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-2xl font-bold text-sm hover:shadow-lg hover:shadow-emerald-500/25 transition-all duration-300 active:scale-[0.98]">
                  确认下单（自动支付）
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
