import { useEffect, useState } from "react";
import { api } from "../api";

interface Order {
  id: number;
  total_amount: number;
  status: string;
  address: string;
  created_at: string;
}

const STATUS_MAP: Record<string, string> = {
  pending: "待支付",
  paid: "已支付",
  shipped: "已发货",
  delivered: "已签收",
  cancelled: "已取消",
};

const STATUS_COLOR: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  paid: "bg-green-100 text-green-700",
  shipped: "bg-blue-100 text-blue-700",
  delivered: "bg-gray-100 text-gray-700",
  cancelled: "bg-red-100 text-red-700",
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

  const handlePay = async (id: number) => {
    await api.payOrder(id);
    load();
  };

  const handleCancel = async (id: number) => {
    await api.cancelOrder(id);
    load();
  };

  if (loading) return <p className="text-center text-gray-400 py-20">加载中...</p>;

  return (
    <div>
      <h2 className="text-lg font-bold mb-4">我的订单</h2>
      {orders.length === 0 ? (
        <p className="text-gray-400 text-center py-20">暂无订单</p>
      ) : (
        <div className="space-y-3">
          {orders.map((o) => (
            <div key={o.id} className="bg-white rounded-xl border p-4 flex items-center justify-between">
              <div>
                <p className="font-semibold">订单 #{o.id}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {o.address} · ¥{o.total_amount} · {o.created_at?.slice(0, 19)}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${STATUS_COLOR[o.status] || ""}`}>
                  {STATUS_MAP[o.status] || o.status}
                </span>
                {o.status === "pending" && (
                  <>
                    <button onClick={() => handlePay(o.id)} className="text-sm text-blue-600 hover:underline">
                      支付
                    </button>
                    <button onClick={() => handleCancel(o.id)} className="text-sm text-red-400 hover:underline">
                      取消
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
