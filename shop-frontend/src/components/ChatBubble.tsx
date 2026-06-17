export default function ChatBubble({ role, text }: { role: "user" | "ai"; text: string }) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"} mb-3 animate-fade-in-up opacity-0`}>
      <div
        className={`max-w-[75%] px-5 py-3 text-sm leading-relaxed ${
          role === "user"
            ? "bg-gradient-to-br from-[#1a1a2e] to-[#222244] text-white rounded-2xl rounded-br-md shadow-lg"
            : "bg-white text-gray-700 rounded-2xl rounded-bl-md shadow-sm border border-gray-50"
        }`}
      >
        {role === "ai" && (
          <div className="flex items-center gap-2 mb-1.5">
            <div className="w-5 h-5 rounded-lg bg-gradient-to-br from-[#1a1a2e] to-[#e94560] flex items-center justify-center text-[10px] text-white font-bold">ZH</div>
            <span className="text-[10px] text-gray-400 font-semibold uppercase tracking-wide">智居助手</span>
          </div>
        )}
        <p className="whitespace-pre-wrap">{text}</p>
      </div>
    </div>
  );
}
