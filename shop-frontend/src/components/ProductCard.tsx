interface Product {
  id: number;
  name: string;
  price: number;
  stock: number;
  description?: string;
  image_url?: string;
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
  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all duration-200">
      <div className="aspect-square bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center text-5xl">
        {product.image_url ? (
          <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
        ) : (
          "📦"
        )}
      </div>
      <div className="p-4">
        <h3
          className="font-semibold text-gray-800 mb-1 cursor-pointer hover:text-blue-600 line-clamp-1"
          onClick={() => onDetail(product)}
        >
          {product.name}
        </h3>
        {product.description && (
          <p className="text-xs text-gray-400 mb-2 line-clamp-2">{product.description}</p>
        )}
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold text-amber-600">¥{product.price}</span>
          <button
            onClick={() => onAddCart(product)}
            className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 transition-colors"
          >
            加入购物车
          </button>
        </div>
        {product.stock <= 10 && (
          <p className="text-xs text-red-400 mt-1">仅剩 {product.stock} 件</p>
        )}
      </div>
    </div>
  );
}
