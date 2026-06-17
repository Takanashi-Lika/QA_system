import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";

export default function AuthModal({ onClose }: { onClose: () => void }) {
  const { login } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");

  const submit = async () => {
    setError("");
    try {
      if (mode === "register") {
        const r = await api.register(email, password, nickname);
        if (r.code !== 0) { setError(r.message); return; }
      }
      const r = await api.login(email, password);
      if (r.code !== 0) { setError(r.message); return; }
      login(r.data.token, { user_id: r.data.user.id, email: r.data.user.email, role: r.data.user.role });
      onClose();
    } catch {
      setError("网络错误");
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white rounded-2xl p-8 w-96 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold mb-6">{mode === "login" ? "登录" : "注册"}</h2>
        {error && <p className="text-red-500 text-sm mb-3">{error}</p>}
        <div className="space-y-4">
          <input className="w-full px-4 py-2 border rounded-lg text-sm" placeholder="邮箱" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="w-full px-4 py-2 border rounded-lg text-sm" type="password" placeholder="密码" value={password} onChange={(e) => setPassword(e.target.value)} />
          {mode === "register" && (
            <input className="w-full px-4 py-2 border rounded-lg text-sm" placeholder="昵称" value={nickname} onChange={(e) => setNickname(e.target.value)} />
          )}
          <button onClick={submit} className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">
            {mode === "login" ? "登录" : "注册"}
          </button>
        </div>
        <p className="text-sm text-gray-400 mt-4 text-center">
          {mode === "login" ? "还没有账号？" : "已有账号？"}
          <button className="text-blue-600 ml-1" onClick={() => setMode(mode === "login" ? "register" : "login")}>
            {mode === "login" ? "去注册" : "去登录"}
          </button>
        </p>
      </div>
    </div>
  );
}
