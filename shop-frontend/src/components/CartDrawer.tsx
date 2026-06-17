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
      <div
        className="w-[420px] bg-white h-full shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h3 className="text-lg font-bold">购物车</h3>
          <button onClick={onClose} className="text-gray-400 text-xl">&times;</button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {items.length === 0 ? (
            <p className="text-gray-400 text-center mt-20">购物车是空的</p>
          ) : (
            items.map((item) => (
              <div key={item.product_id} className="flex items-center justify-between py-3 border-b">
                <div className="flex-1">
                  <p className="font-medium text-sm">{item.product_name}</p>
                  <p className="text-amber-600 font-bold">¥{item.price}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    className="w-7 h-7 rounded-full border text-sm"
                    onClick={() => onUpdateQty(item.product_id, item.quantity - 1)}
                  >
                    -
                  </button>
                  <span className="w-6 text-center">{item.quantity}</span>
                  <button
                    className="w-7 h-7 rounded-full border text-sm"
                    onClick={() => onUpdateQty(item.product_id, item.quantity + 1)}
                  >
                    +
                  </button>
                  <button className="ml-2 text-red-400 text-xs" onClick={() => onRemove(item.product_id)}>
                    删除
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {items.length > 0 && (
          <div className="px-6 py-4 border-t bg-gray-50">
            <div className="flex justify-between text-lg font-bold mb-3">
              <span>合计</span>
              <span className="text-amber-600">¥{total}</span>
            </div>
            {!showCheckout ? (
              <button
                onClick={() => {
                  if (!user) { alert("请先登录"); return; }
                  setShowCheckout(true);
                }}
                className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700"
              >
                去结算
              </button>
            ) : (
              <div>
                <input
                  className="w-full px-4 py-2 border rounded-lg text-sm mb-3"
                  placeholder="收货地址"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                />
                <button
                  onClick={() => onCheckout(address)}
                  className="w-full py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700"
                >
                  确认下单（模拟支付）
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
