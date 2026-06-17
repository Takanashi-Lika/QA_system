import { useEffect, useState } from "react";
import { api } from "../api";
import ProductCard from "../components/ProductCard";

interface Product {
  id: number;
  name: string;
  price: number;
  stock: number;
  description?: string;
}

interface Category {
  id: number;
  name: string;
  children?: Category[];
}

const CAT_ICONS: Record<string, string> = {
  "门锁": "🔐", "智能门锁": "🔐",
  "摄像头": "📷", "智能摄像头": "📷",
  "网关": "🌐", "智能网关": "🌐",
  "灯具": "💡", "智能灯具": "💡",
  "窗帘": "🪟", "智能窗帘": "🪟",
  "传感器": "📡",
};

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="bg-white rounded-2xl overflow-hidden">
          <div className="skeleton aspect-[4/3]" />
          <div className="p-4 space-y-2">
            <div className="skeleton h-4 w-3/4" />
            <div className="skeleton h-3 w-full" />
            <div className="skeleton h-5 w-1/3 mt-3" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function HomeTab({
  onDetail,
  onAddCart,
}: {
  onDetail: (p: Product) => void;
  onAddCart: (p: Product) => void;
}) {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [activeCat, setActiveCat] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const loadProducts = async (catId?: number | null, kw?: string) => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (kw) params.keyword = kw;
    else if (catId) params.category_id = String(catId);
    const r = await api.getProducts(Object.keys(params).length ? params : undefined);
    const data = r.data;
    if (Array.isArray(data)) setProducts(data);
    else if (data?.items) setProducts(data.items);
    else setProducts([]);
    setLoading(false);
  };

  useEffect(() => {
    api.getCategoryTree().then((r) => {
      if (r.code === 0) setCategories(r.data || []);
    });
    loadProducts();
  }, []);

  useEffect(() => {
    loadProducts(activeCat);
  }, [activeCat]);

  return (
    <div>
      <div className="mb-8">
        <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-[#1a1a2e] via-[#222244] to-[#e94560] p-8 md:p-10 text-white">
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-10 right-20 text-[160px] select-none">🏠</div>
            <div className="absolute bottom-0 left-10 text-[100px] select-none">🔐</div>
            <div className="absolute top-20 right-[40%] text-[80px] select-none">💡</div>
          </div>
          <div className="relative z-10">
            <h1 className="text-3xl md:text-4xl font-extrabold mb-2 tracking-tight">
              让你的家更智能
            </h1>
            <p className="text-white/70 text-sm md:text-base max-w-md mb-6">
              从门锁到灯光，从摄像头到窗帘 — 一站式智能家居购物体验
            </p>
            <div className="flex gap-3">
              {["门锁", "摄像头", "灯具", "传感器"].map((kw) => (
                <button
                  key={kw}
                  className="px-5 py-2 bg-white/15 backdrop-blur rounded-2xl text-sm font-medium hover:bg-white/25 transition-all active:scale-95 border border-white/10"
                  onClick={() => { setActiveCat(null); loadProducts(null, kw); }}
                >
                  {kw}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 md:grid-cols-6 gap-3 mb-8">
        <button
          className={`px-4 py-3 rounded-2xl text-sm font-semibold transition-all duration-200 ${
            activeCat === null
              ? "bg-[#1a1a2e] text-white shadow-lg shadow-[#1a1a2e]/20"
              : "bg-white text-gray-600 hover:bg-gray-50 shadow-sm border border-gray-50"
          }`}
          onClick={() => setActiveCat(null)}
        >
          全部商品
        </button>
        {categories.map((cat) => {
          const icon = Object.entries(CAT_ICONS).find(([k]) => cat.name.includes(k))?.[1];
          return (
            <button
              key={cat.id}
              className={`px-4 py-3 rounded-2xl text-sm font-semibold transition-all duration-200 ${
                activeCat === cat.id
                  ? "bg-[#1a1a2e] text-white shadow-lg shadow-[#1a1a2e]/20"
                  : "bg-white text-gray-600 hover:bg-gray-50 shadow-sm border border-gray-50"
              }`}
              onClick={() => setActiveCat(cat.id)}
            >
              {icon && <span className="mr-1">{icon}</span>}
              {cat.name}
            </button>
          );
        })}
      </div>

      {loading ? (
        <SkeletonGrid />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
          {products.map((p, i) => (
            <div key={p.id} style={{ animationDelay: `${i * 60}ms` }} className="animate-fade-in-up opacity-0">
              <ProductCard product={p} onDetail={onDetail} onAddCart={onAddCart} />
            </div>
          ))}
          {products.length === 0 && (
            <p className="col-span-full text-center text-gray-400 py-20">暂无商品</p>
          )}
        </div>
      )}
    </div>
  );
}
