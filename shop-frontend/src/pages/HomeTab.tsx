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
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        <button
          className={`px-4 py-2 rounded-full text-sm whitespace-nowrap ${
            activeCat === null ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
          onClick={() => setActiveCat(null)}
        >
          全部
        </button>
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={`px-4 py-2 rounded-full text-sm whitespace-nowrap ${
              activeCat === cat.id ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
            onClick={() => setActiveCat(cat.id)}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-center text-gray-400 py-20">加载中...</p>
      ) : (
        <div className="grid grid-cols-4 gap-5">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} onDetail={onDetail} onAddCart={onAddCart} />
          ))}
          {products.length === 0 && (
            <p className="col-span-4 text-center text-gray-400 py-20">暂无商品</p>
          )}
        </div>
      )}
    </div>
  );
}
