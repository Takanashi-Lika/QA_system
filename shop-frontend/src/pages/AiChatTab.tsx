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
    { role: "ai", text: "你好！我是智居智能助手，可以直接问我产品问题，也可以帮你搜索、下单。" },
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
        reply += "\n\n---\n🔧";
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
        {loading && <ChatBubble role="ai" text="思考中..." />}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2 mb-3 flex-wrap">
        {PROMPTS.map((p) => (
          <button
            key={p}
            className="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-full text-xs hover:bg-blue-50 hover:text-blue-600"
            onClick={() => send(p)}
          >
            {p}
          </button>
        ))}
      </div>

      <div className="flex gap-3">
        <input
          className="flex-1 px-4 py-3 border rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-400"
          placeholder="问我产品问题，或让我帮你下单..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(input)}
        />
        <button
          className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50"
          onClick={() => send(input)}
          disabled={loading}
        >
          发送
        </button>
      </div>
    </div>
  );
}
