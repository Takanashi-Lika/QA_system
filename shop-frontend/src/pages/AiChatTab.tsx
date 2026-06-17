import { useState, useRef, useEffect } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import ChatBubble from "../components/ChatBubble";

interface Message {
  role: "user" | "ai";
  text: string;
}

const PROMPTS = ["帮我买个门锁", "门锁没电了怎么办", "有哪些摄像头", "摄像头怎么安装", "查看我的订单"];

export default function AiChatTab() {
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    { role: "ai", text: "你好！我是智居智能助手 ✨\n可以直接问我产品问题，也可以帮你搜索商品、下单。" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<{ role: string; content: string }[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const newHistory = [...history, { role: "user", content: text }];
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      const r = await api.unifiedChat(newHistory, token);
      let reply = r.response || "抱歉，当前服务不可用。";
      if (r.tool_calls?.length) {
        reply += "\n\n⸻\n🔧";
        r.tool_calls.forEach((tc: { name: string; args: Record<string, unknown> }) => {
          reply += `\n• ${tc.name}(${JSON.stringify(tc.args)})`;
        });
      }
      setMessages((m) => [...m, { role: "ai", text: reply }]);
      setHistory([...newHistory, { role: "assistant", content: r.response || "" }]);
    } catch {
      setMessages((m) => [...m, { role: "ai", text: "抱歉，服务连接失败。" }]);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)]">
      <div className="flex-1 overflow-y-auto mb-4 pr-2">
        {messages.map((m, i) => (
          <ChatBubble key={i} role={m.role} text={m.text} />
        ))}
        {loading && (
          <div className="flex justify-start mb-3">
            <div className="bg-white rounded-2xl rounded-bl-md px-4 py-3 shadow-sm border border-gray-50">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2 mb-3 flex-wrap">
        {PROMPTS.map((p) => (
          <button
            key={p}
            className="px-3.5 py-2 bg-white text-gray-600 rounded-2xl text-xs font-medium hover:bg-[#1a1a2e] hover:text-white transition-all duration-200 shadow-sm border border-gray-50 active:scale-95"
            onClick={() => send(p)}
          >
            {p}
          </button>
        ))}
      </div>

      <div className="flex gap-3">
        <input
          className="flex-1 px-5 py-3.5 bg-white border border-gray-100 rounded-2xl text-sm outline-none focus:border-[#1a1a2e]/20 focus:ring-4 focus:ring-[#1a1a2e]/5 transition-all shadow-sm placeholder:text-gray-400"
          placeholder="问我产品问题，或让我帮你下单..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(input)}
        />
        <button
          className="px-6 py-3.5 bg-gradient-to-r from-[#1a1a2e] to-[#e94560] text-white rounded-2xl font-bold text-sm hover:shadow-lg hover:shadow-[#e94560]/25 transition-all duration-300 active:scale-95 disabled:opacity-50"
          onClick={() => send(input)}
          disabled={loading}
        >
          发送
        </button>
      </div>
    </div>
  );
}
