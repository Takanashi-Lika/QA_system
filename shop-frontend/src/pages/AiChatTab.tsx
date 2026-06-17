import { useState, useRef, useEffect } from "react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import ChatBubble from "../components/ChatBubble";

interface Message {
  role: "user" | "ai";
  text: string;
}

type ChatMode = "faq" | "agent";

const FAQ_PROMPTS = ["门锁没电了怎么办", "摄像头怎么安装", "网关能连几个设备", "怎么申请售后"];
const AGENT_PROMPTS = ["帮我买个门锁", "有哪些摄像头", "帮我推荐一个网关", "查看我的订单", "我要下单"];

export default function AiChatTab() {
  const { token } = useAuth();
  const [mode, setMode] = useState<ChatMode>("faq");
  const [messages, setMessages] = useState<Message[]>([
    { role: "ai", text: "你好！我是智居智能客服，有什么可以帮你的？" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<{ role: string; content: string }[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const switchMode = (m: ChatMode) => {
    setMode(m);
    if (m === "agent" && !token) {
      setMessages([{ role: "ai", text: "需要先登录才能使用购物助手。请先在首页点击「登录/注册」。" }]);
    } else {
      setMessages([{ role: "ai", text: m === "faq"
        ? "你好！我是智居FAQ客服，可以问我产品相关问题。"
        : "你好！我是智居购物助手，直接告诉我你想买什么就行。" }
      ]);
    }
    setHistory([]);
  };

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const newHistory = [...history, { role: "user", content: text }];
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      if (mode === "faq") {
        const r = await api.aiChat(text);
        const reply = r.answer || "抱歉，服务暂时不可用。";
        setMessages((m) => [...m, { role: "ai", text: reply }]);
        setHistory([...newHistory, { role: "assistant", content: reply }]);
      } else {
        const r = await api.agentChat(newHistory, token);
        const reply = r.response || "抱歉，服务暂时不可用。";
        let fullText = reply;
        if (r.tool_calls?.length) {
          fullText += "\n\n---\n🔧 执行了以下操作：\n";
          r.tool_calls.forEach((tc: { name: string; args: Record<string, unknown>; result: string }) => {
            fullText += `\n• **${tc.name}**(${JSON.stringify(tc.args)})`;
          });
        }
        setMessages((m) => [...m, { role: "ai", text: fullText }]);
        setHistory([...newHistory, { role: "assistant", content: reply }]);
      }
    } catch {
      setMessages((m) => [...m, { role: "ai", text: "抱歉，服务连接失败。" }]);
    }
    setLoading(false);
  };

  const prompts = mode === "faq" ? FAQ_PROMPTS : AGENT_PROMPTS;

  return (
    <div className="flex flex-col h-[calc(100vh-140px)]">
      <div className="flex items-center gap-3 mb-3">
        <button
          className={`px-4 py-1.5 rounded-full text-xs font-medium ${mode === "faq" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600"}`}
          onClick={() => switchMode("faq")}
        >
          📖 FAQ客服
        </button>
        <button
          className={`px-4 py-1.5 rounded-full text-xs font-medium ${mode === "agent" ? "bg-green-600 text-white" : "bg-gray-100 text-gray-600"}`}
          onClick={() => switchMode("agent")}
        >
          🛒 智能购物
        </button>
      </div>

      <div className="flex-1 overflow-y-auto mb-4 pr-2">
        {messages.map((m, i) => (
          <ChatBubble key={i} role={m.role} text={m.text} />
        ))}
        {loading && <ChatBubble role="ai" text="思考中..." />}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2 mb-3 flex-wrap">
        {prompts.map((p) => (
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
          placeholder={mode === "faq" ? "输入FAQ问题..." : "输入购物需求，如'帮我买个门锁'..."}
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
