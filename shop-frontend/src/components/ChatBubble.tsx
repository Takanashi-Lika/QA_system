export default function ChatBubble({ role, text }: { role: "user" | "ai"; text: string }) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm ${
          role === "user"
            ? "bg-blue-600 text-white rounded-br-md"
            : "bg-gray-100 text-gray-800 rounded-bl-md"
        }`}
      >
        {role === "ai" && <div className="text-xs text-blue-500 mb-1">🤖 智能客服</div>}
        <p className="whitespace-pre-wrap">{text}</p>
      </div>
    </div>
  );
}
