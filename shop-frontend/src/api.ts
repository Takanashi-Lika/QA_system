const API_BASE = "http://localhost:8001";
const RAG_BASE = "http://localhost:8000";

function token() {
  return localStorage.getItem("token") || "";
}

function headers() {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token()) h["Authorization"] = `Bearer ${token()}`;
  return h;
}

async function request(method: string, path: string, body?: unknown) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

export const api = {
  register: (email: string, password: string, nickname: string) =>
    request("POST", "/c-endpoint/register", { email, password, nickname }),

  login: (email: string, password: string) =>
    request("POST", "/c-endpoint/login", { email, password }),

  getMe: () => request("GET", "/c-endpoint/me"),

  updateAddress: (address: string) =>
    request("PUT", "/c-endpoint/address", { address }),

  getHotProducts: () => request("GET", "/c-endpoint/products/hot"),

  getProducts: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request("GET", `/c-endpoint/products${qs}`);
  },

  getProductDetail: (id: number) =>
    request("GET", `/c-endpoint/products/${id}`),

  getCategoryTree: () => request("GET", "/b-endpoint/categories/"),

  getCart: () => request("GET", "/c-endpoint/cart/"),

  addToCart: (productId: number, quantity: number) =>
    request("POST", "/c-endpoint/cart/", { product_id: productId, quantity }),

  updateCartItem: (productId: number, quantity: number) =>
    request("PUT", `/c-endpoint/cart/${productId}`, { quantity }),

  removeFromCart: (productId: number) =>
    request("DELETE", `/c-endpoint/cart/${productId}`),

  createOrder: (address: string) =>
    request("POST", "/c-endpoint/orders/", { address }),

  getOrders: (status?: string) =>
    request("GET", `/c-endpoint/orders/${status ? `?status=${status}` : ""}`),

  getOrderDetail: (id: number) =>
    request("GET", `/c-endpoint/orders/${id}`),

  payOrder: (id: number) =>
    request("POST", `/c-endpoint/orders/${id}/pay`),

  cancelOrder: (id: number) =>
    request("DELETE", `/c-endpoint/orders/${id}`),

  getLogistics: (orderId?: number) =>
    request("GET", `/c-endpoint/logistics${orderId ? `?order_id=${orderId}` : ""}`),

  getAfterSales: () => request("GET", "/c-endpoint/after-sales"),

  createAfterSale: (orderId: number, type: string, reason: string) =>
    request("POST", "/c-endpoint/after-sales", { order_id: orderId, type, reason }),

  aiChat: (question: string) =>
    fetch(`${RAG_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }).then((r) => r.json()),

  unifiedChat: (messages: { role: string; content: string }[], userToken: string) =>
    fetch(`${RAG_BASE}/api/chat/unified`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages, user_token: userToken }),
    }).then((r) => r.json()),
};
