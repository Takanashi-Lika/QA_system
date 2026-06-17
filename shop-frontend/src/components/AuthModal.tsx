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
      login(r.data.token, { user_id: r.data.user.id ?? r.data.user?.id, email: r.data.user.email ?? r.data.user?.email, role: r.data.user.role });
      onClose();
    } catch {
      setError("网络错误");
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center animate-fade-in" onClick={onClose}>
      <div className="bg-white rounded-3xl p-8 w-[420px] shadow-2xl animate-scale-in" onClick={(e) => e.stopPropagation()}>
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#1a1a2e] to-[#e94560] flex items-center justify-center text-white text-xl font-extrabold mx-auto mb-4">
            ZH
          </div>
          <h2 className="text-2xl font-extrabold text-[#1a1a2e]">{mode === "login" ? "欢迎回来" : "创建账号"}</h2>
          <p className="text-sm text-gray-400 mt-1">{mode === "login" ? "登录你的智居账号" : "开启智能家居之旅"}</p>
        </div>
        {error && (
          <div className="mb-4 px-4 py-2.5 bg-red-50 border border-red-100 rounded-2xl text-red-500 text-sm">{error}</div>
        )}
        <div className="space-y-3.5">
          <input className="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-2xl text-sm outline-none focus:bg-white focus:border-[#1a1a2e]/20 focus:ring-4 focus:ring-[#1a1a2e]/5 transition-all" placeholder="邮箱地址" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-2xl text-sm outline-none focus:bg-white focus:border-[#1a1a2e]/20 focus:ring-4 focus:ring-[#1a1a2e]/5 transition-all" type="password" placeholder="密码" value={password} onChange={(e) => setPassword(e.target.value)} />
          {mode === "register" && (
            <input className="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-2xl text-sm outline-none focus:bg-white focus:border-[#1a1a2e]/20 focus:ring-4 focus:ring-[#1a1a2e]/5 transition-all" placeholder="昵称" value={nickname} onChange={(e) => setNickname(e.target.value)} />
          )}
          <button onClick={submit} className="w-full py-3 bg-gradient-to-r from-[#1a1a2e] to-[#e94560] text-white rounded-2xl font-semibold text-sm hover:shadow-lg hover:shadow-[#e94560]/25 transition-all duration-300 active:scale-[0.98]">
            {mode === "login" ? "登 录" : "注 册"}
          </button>
        </div>
        <p className="text-sm text-gray-400 mt-6 text-center">
          {mode === "login" ? "还没有账号？" : "已有账号？"}
          <button className="text-[#e94560] font-semibold ml-1 hover:underline" onClick={() => setMode(mode === "login" ? "register" : "login")}>
            {mode === "login" ? "立即注册" : "去登录"}
          </button>
        </p>
      </div>
    </div>
  );
}
