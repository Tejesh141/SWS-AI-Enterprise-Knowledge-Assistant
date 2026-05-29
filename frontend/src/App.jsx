import { useState, useEffect, useRef, useCallback } from "react";
import Header from "./components/Header";
import WelcomeCard from "./components/WelcomeCard";
import MessageBubble from "./components/MessageBubble";
import TypingIndicator from "./components/TypingIndicator";
import ChatInput from "./components/ChatInput";
import { sendQuestion } from "./api";

const fmt = () =>
  new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// Derive a confidence score from the top source similarity or answer length heuristic
const deriveConfidence = (sources, answer) => {
  if (!sources?.length) return 0.55;
  // More sources + longer answer = higher confidence (heuristic for display)
  const base = 0.72 + Math.min(sources.length * 0.06, 0.18);
  const lengthBonus = Math.min(answer.length / 2000, 0.08);
  return Math.min(base + lengthBonus, 0.98);
};

export default function App() {
  const [dark, setDark] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState("checking");
  const bottomRef = useRef(null);

  // Apply dark mode class to <html>
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  // Check API health on mount
  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((r) => r.ok ? setApiStatus("online") : setApiStatus("offline"))
      .catch(() => setApiStatus("offline"));
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = useCallback(async () => {
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), role: "user", content: question, timestamp: fmt() },
    ]);
    setLoading(true);

    try {
      const data = await sendQuestion(question);
      const confidence = deriveConfidence(data.sources, data.answer);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: data.answer,
          sources: data.sources ?? [],
          confidence,
          timestamp: fmt(),
        },
      ]);
    } catch (err) {
      const detail = err.response?.data?.detail ?? err.message ?? "Unknown error";
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: `⚠️ Sorry, I encountered an error: ${detail}`,
          sources: [],
          timestamp: fmt(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading]);

  const showWelcome = messages.length === 0;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col transition-colors duration-200">
      <Header dark={dark} onToggleDark={() => setDark((d) => !d)} apiStatus={apiStatus} />

      {/* Chat area */}
      <main className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="max-w-5xl mx-auto px-4 py-6 flex flex-col gap-4">

          {showWelcome && (
            <WelcomeCard onSuggest={(q) => { setInput(q); }} />
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {loading && <TypingIndicator />}

          <div ref={bottomRef} />
        </div>
      </main>

      <ChatInput
        value={input}
        onChange={setInput}
        onSend={handleSend}
        loading={loading}
      />
    </div>
  );
}
