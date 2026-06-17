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
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded-2xl p-0 w-[480px] overflow-hidden shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="aspect-video bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center text-7xl">
          📦
        </div>
        <div className="p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">{product.name}</h2>
          <p className="text-3xl font-bold text-amber-600 mb-4">¥{product.price}</p>
          {product.description && <p className="text-sm text-gray-500 mb-4">{product.description}</p>}
          <p className="text-sm text-gray-500 mb-4">库存：{product.stock} 件</p>

          {inCart ? (
            <div className="flex items-center gap-3">
              <button
                className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center"
                onClick={() => onUpdateQty(product.id, inCart.quantity - 1)}
              >
                -
              </button>
              <span className="font-semibold">{inCart.quantity}</span>
              <button
                className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center"
                onClick={() => onUpdateQty(product.id, inCart.quantity + 1)}
              >
                +
              </button>
              <span className="text-sm text-gray-400 ml-2">（已在购物车中）</span>
            </div>
          ) : (
            <button
              className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700"
              onClick={() => onAddCart(product)}
            >
              加入购物车
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
