import { useState, useRef, useEffect } from "react";
import { api } from "../api";
import ChatBubble from "../components/ChatBubble";

interface Message {
  role: "user" | "ai";
  text: string;
}

const PROMPTS = ["门锁没电了怎么办", "摄像头怎么安装", "网关能连几个设备", "怎么申请售后", "门锁识別失败怎么办"];

export default function AiChatTab() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "ai", text: "你好！我是智居智能客服，有什么可以帮你的？" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);
    try {
      const r = await api.aiChat(text);
      setMessages((m) => [...m, { role: "ai", text: r.answer || "抱歉，服务暂时不可用。" }]);
    } catch {
      setMessages((m) => [...m, { role: "ai", text: "抱歉，AI 服务连接失败。" }]);
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
          placeholder="输入问题..."
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
