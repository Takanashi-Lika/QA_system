interface Product {
  id: number;
  name: string;
  price: number;
  stock: number;
  description?: string;
  image_url?: string;
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

const COLOR_MAP = [
  "from-indigo-50 to-blue-100",
  "from-rose-50 to-pink-100",
  "from-amber-50 to-yellow-100",
  "from-emerald-50 to-teal-100",
  "from-violet-50 to-purple-100",
  "from-cyan-50 to-sky-100",
  "from-orange-50 to-red-100",
  "from-lime-50 to-green-100",
];

function getEmoji(name: string) {
  for (const [k, v] of Object.entries(EMOJI_MAP)) {
    if (name.includes(k)) return v;
  }
  return "📦";
}

function getGradient(id: number) {
  return COLOR_MAP[id % COLOR_MAP.length];
}

function getImageUrl(product: Product) {
  if (product.image_url) return product.image_url;
  if (product.name.includes("X1 智能指纹门锁")) return "/products/x1-fingerprint-lock.png";
  if (product.name.includes("X2") && product.name.includes("人脸")) return "/products/x2-face-lock.png";
  if (product.name.includes("X3") && product.name.includes("猫眼")) return "/products/x3-cat-eye-lock.png";
  if (product.name.includes("C1") && product.name.includes("摄像头")) return "/products/c1-indoor-camera.png";
  if (product.name.includes("G1") && product.name.includes("网关")) return "/products/g1-home-gateway.png";
  if (product.name.includes("G2") && product.name.includes("网关")) return "/products/g2-hub-gateway.png";
  return "";
}

export default function ProductCard({
  product,
  onDetail,
  onAddCart,
}: {
  product: Product;
  onDetail: (p: Product) => void;
  onAddCart: (p: Product) => void;
}) {
  const emoji = getEmoji(product.name);
  const gradient = getGradient(product.id);
  const imageUrl = getImageUrl(product);

  return (
    <div className="card-hover bg-white rounded-2xl overflow-hidden border border-gray-50 cursor-pointer group">
      <div
        className={`aspect-[4/3] bg-gradient-to-br ${gradient} flex items-center justify-center text-6xl relative overflow-hidden`}
        onClick={() => onDetail(product)}
      >
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={product.name}
            className="w-full h-full object-contain p-5 transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <span className="transition-transform duration-300 group-hover:scale-110">{emoji}</span>
        )}
        {product.stock <= 15 && (
          <span className="absolute top-3 left-3 px-2.5 py-1 bg-white/90 backdrop-blur rounded-full text-[10px] font-bold text-[#e94560] shadow-sm">
            仅剩 {product.stock} 件
          </span>
        )}
        <div className="card-accent absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-[#1a1a2e] to-[#e94560]" />
      </div>
      <div className="p-4">
        <h3
          className="font-bold text-[#1a1a2e] mb-1 line-clamp-1 text-[15px] group-hover:text-[#e94560] transition-colors"
          onClick={() => onDetail(product)}
        >
          {product.name}
        </h3>
        {product.description && (
          <p className="text-xs text-gray-400 mb-3 line-clamp-2 leading-relaxed">{product.description}</p>
        )}
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs text-gray-400">¥</span>
            <span className="text-xl font-extrabold text-[#1a1a2e]">{product.price}</span>
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); onAddCart(product); }}
            className="px-4 py-2 bg-[#1a1a2e] text-white text-xs font-semibold rounded-xl hover:bg-[#e94560] transition-all duration-300 active:scale-95 shadow-sm hover:shadow-md"
          >
            加入购物车
          </button>
        </div>
      </div>
    </div>
  );
}
