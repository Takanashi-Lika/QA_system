import { useEffect, useState } from "react";
import { api } from "../api";

interface Order {
  id: number;
  total_amount: number;
  status: string;
  address: string;
  created_at: string;
}

const STATUS_MAP: Record<string, { label: string; color: string; bg: string }> = {
  pending: { label: "待支付", color: "text-yellow-600", bg: "bg-yellow-50" },
  paid: { label: "已支付", color: "text-green-600", bg: "bg-green-50" },
  shipped: { label: "已发货", color: "text-blue-600", bg: "bg-blue-50" },
  delivered: { label: "已签收", color: "text-gray-600", bg: "bg-gray-50" },
  cancelled: { label: "已取消", color: "text-red-500", bg: "bg-red-50" },
};

export default function OrdersTab() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const r = await api.getOrders();
    if (r.code === 0) setOrders(r.data?.items || []);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handlePay = async (id: number) => { await api.payOrder(id); load(); };
  const handleCancel = async (id: number) => { await api.cancelOrder(id); load(); };

  return (
    <div>
      <h2 className="text-xl font-extrabold text-[#1a1a2e] mb-6">我的订单</h2>
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-2xl p-5 space-y-3">
              <div className="skeleton h-4 w-1/4" />
              <div className="skeleton h-3 w-1/2" />
            </div>
          ))}
        </div>
      ) : orders.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-5xl mb-4 opacity-30">📋</div>
          <p className="text-gray-400">暂无订单，去逛逛吧</p>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map((o) => {
            const st = STATUS_MAP[o.status] || STATUS_MAP.pending;
            return (
              <div key={o.id} className="bg-white rounded-2xl p-5 border border-gray-50 hover:shadow-md transition-shadow duration-200 animate-fade-in-up opacity-0">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <span className="font-bold text-[#1a1a2e]">订单 #{o.id}</span>
                    <span className={`ml-3 px-3 py-1 rounded-full text-xs font-semibold ${st.color} ${st.bg}`}>{st.label}</span>
                  </div>
                  <span className="text-xl font-extrabold text-[#1a1a2e]">¥{o.total_amount}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">{o.address} · {o.created_at?.slice(0, 19)}</span>
                  <div className="flex gap-2">
                    {o.status === "pending" && (
                      <>
                        <button onClick={() => handlePay(o.id)} className="px-4 py-1.5 bg-gradient-to-r from-[#1a1a2e] to-[#e94560] text-white rounded-full text-xs font-semibold hover:shadow-md transition-shadow">支付</button>
                        <button onClick={() => handleCancel(o.id)} className="px-4 py-1.5 border border-gray-200 text-gray-400 rounded-full text-xs hover:text-[#e94560] hover:border-[#e94560] transition-colors">取消</button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
