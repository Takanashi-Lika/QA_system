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

const EMOJI_MAP: Record<string, string> = {
  "门锁": "🔐", "指纹": "🔐", "人脸": "🔐", "猫眼": "🔐",
  "摄像头": "📷", "摄像": "📷",
  "网关": "🌐", "中枢": "🌐",
  "传感器": "📡", "门磁": "📡", "人体": "🚶", "温湿度": "🌡️", "水浸": "💧", "烟雾": "🔥",
  "灯": "💡", "吸顶灯": "💡", "灯带": "🌈", "灯泡": "💡",
  "窗帘": "🪟", "卷帘": "🪟",
  "适配器": "🔌", "中继器": "📶",
};

function getEmoji(name: string) {
  for (const [k, v] of Object.entries(EMOJI_MAP)) {
    if (name.includes(k)) return v;
  }
  return "📦";
}

export default function ProductDetail({
  product,
  cartItems,
  onClose,
  onAddCart,
  onUpdateQty,
}: {
  product: Product;
  cartItems: CartItem[];
  onClose: () => void;
  onAddCart: (p: Product) => void;
  onUpdateQty: (id: number, qty: number) => void;
}) {
  const inCart = cartItems.find((c) => c.product_id === product.id);

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center animate-fade-in" onClick={onClose}>
      <div className="bg-white rounded-3xl w-[500px] overflow-hidden shadow-2xl animate-scale-in" onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} className="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/80 backdrop-blur flex items-center justify-center text-gray-500 hover:text-[#1a1a2e] z-10 transition-colors text-lg">&times;</button>

        <div className="aspect-video bg-gradient-to-br from-indigo-50 via-rose-50 to-amber-50 flex items-center justify-center text-8xl relative">
          <span className="animate-float" style={{ animationDuration: "3s" }}>{getEmoji(product.name)}</span>
        </div>

        <div className="p-8">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-2xl font-extrabold text-[#1a1a2e] mb-1">{product.name}</h2>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">¥</span>
                <span className="text-3xl font-extrabold text-[#1a1a2e]">{product.price}</span>
              </div>
            </div>
            <div className="text-right">
              <div className={`px-3 py-1.5 rounded-full text-xs font-semibold ${product.stock > 20 ? "bg-green-50 text-green-600" : "bg-red-50 text-[#e94560]"}`}>
                {product.stock > 20 ? "有货" : `仅剩 ${product.stock} 件`}
              </div>
            </div>
          </div>

          {product.description && (
            <p className="text-sm text-gray-500 leading-relaxed mb-6 bg-gray-50 p-4 rounded-2xl">{product.description}</p>
          )}

          {inCart ? (
            <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-2xl">
              <span className="text-sm text-gray-500">已在购物车中</span>
              <div className="flex items-center gap-1">
                <button className="w-9 h-9 rounded-xl border-2 border-gray-200 flex items-center justify-center font-bold text-gray-600 hover:border-[#1a1a2e] hover:text-[#1a1a2e] transition-all" onClick={() => onUpdateQty(product.id, inCart.quantity - 1)}>-</button>
                <span className="w-10 text-center font-bold text-[#1a1a2e]">{inCart.quantity}</span>
                <button className="w-9 h-9 rounded-xl border-2 border-gray-200 flex items-center justify-center font-bold text-gray-600 hover:border-[#1a1a2e] hover:text-[#1a1a2e] transition-all" onClick={() => onUpdateQty(product.id, inCart.quantity + 1)}>+</button>
              </div>
            </div>
          ) : (
            <button className="w-full py-3.5 bg-gradient-to-r from-[#1a1a2e] to-[#e94560] text-white rounded-2xl font-bold text-sm hover:shadow-lg hover:shadow-[#e94560]/25 transition-all duration-300 active:scale-[0.98]" onClick={() => onAddCart(product)}>
              加入购物车
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
