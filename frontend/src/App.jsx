import { useState, useEffect, useRef, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Header from "./components/Header";
import WelcomeCard from "./components/WelcomeCard";
import MessageBubble from "./components/MessageBubble";
import TypingIndicator from "./components/TypingIndicator";
import ChatInput from "./components/ChatInput";
import { ToastContainer } from "./components/Toast";
import { sendQuestion, checkHealth } from "./services/api";
import { translateToEnglish, translateFromEnglish } from "./services/translationService";
import { findLocalAnswer } from "./services/knowledgeBase";

const fmt = () =>
  new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const deriveConfidence = (sources, answer) => {
  if (!sources?.length) return 0.72;
  const base = 0.78 + Math.min(sources.length * 0.06, 0.16);
  return Math.min(base + Math.min(answer.length / 2000, 0.06), 0.98);
};

let toastId = 0;

export default function App() {
  const [dark, setDark] = useState(() => window.matchMedia("(prefers-color-scheme: dark)").matches);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState("checking");
  const [language, setLanguage] = useState("en");
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [toasts, setToasts] = useState([]);
  const bottomRef = useRef(null);

  const addToast = useCallback((type, title, message) => {
    const id = ++toastId;
    setToasts((prev) => [...prev, { id, type, title, message }]);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  useEffect(() => {
    checkHealth()
      .then((ok) => setApiStatus(ok ? "online" : "offline"))
      .catch(() => setApiStatus("offline"));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ── Core send logic ────────────────────────────────────────────────────────
  const sendMessage = useCallback(async (rawQuestion) => {
    const question = rawQuestion.trim();
    if (!question || loading) return;

    // 1. Show user bubble immediately
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), role: "user", content: question, timestamp: fmt() },
    ]);
    setLoading(true);

    try {
      // 2. Translate to English for backend/KB lookup
      const englishQ = language !== "en"
        ? await translateToEnglish(question, language)
        : question;

      let answer = null;
      let sources = [];

      // 3a. Try real backend first
      if (apiStatus === "online") {
        try {
          const data = await sendQuestion(englishQ);
          answer = data.answer;
          sources = data.sources ?? [];
        } catch {
          // Backend failed — fall through to local KB
        }
      }

      // 3b. Fallback: local knowledge base
      if (!answer) {
        const local = findLocalAnswer(englishQ);
        if (local) {
          answer = local.answer;
          sources = local.sources;
        }
      }

      // 3c. Nothing matched anywhere
      if (!answer) {
        answer = "I don't have information about that in the company documents. Please contact HR at **hr@sws-ai.com** or check the company intranet for more details.";
        sources = [];
      }

      // 4. Translate answer back if needed
      const displayAnswer = language !== "en"
        ? await translateFromEnglish(answer, language)
        : answer;

      const confidence = deriveConfidence(sources, answer);

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: displayAnswer,
          sources,
          confidence,
          timestamp: fmt(),
        },
      ]);
    } catch (err) {
      // Only show toast for unexpected errors; still give a graceful answer
      addToast("error", "Connection Issue", "Using offline knowledge base.");
      const local = findLocalAnswer(question);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: local?.answer ?? "I don't have information about that in the company documents. Please contact HR at **hr@sws-ai.com**.",
          sources: local?.sources ?? [],
          confidence: local ? 0.82 : 0.5,
          timestamp: fmt(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [loading, language, apiStatus, addToast]);

  const handleSend = useCallback(() => {
    const q = input.trim();
    if (!q) return;
    setInput("");
    sendMessage(q);
  }, [input, sendMessage]);

  const handleSuggest = useCallback((q) => {
    sendMessage(q);
  }, [sendMessage]);

  const showWelcome = messages.length === 0 && !loading;

  return (
    <div
      className="min-h-screen flex flex-col transition-colors duration-300"
      style={{ background: dark ? "#0D0A1A" : "#FAF7FF" }}
    >
      {/* Ambient background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full opacity-20 dark:opacity-10 animate-float"
          style={{ background: "radial-gradient(circle, #A855F7, transparent 70%)" }} />
        <div className="absolute top-1/2 -right-48 w-80 h-80 rounded-full opacity-15 animate-float"
          style={{ background: "radial-gradient(circle, #7C3AED, transparent 70%)", animationDelay: "3s" }} />
        <div className="absolute -bottom-24 left-1/3 w-64 h-64 rounded-full opacity-10 animate-float"
          style={{ background: "radial-gradient(circle, #C084FC, transparent 70%)", animationDelay: "1.5s" }} />
      </div>

      <Header
        dark={dark}
        onToggleDark={() => setDark((d) => !d)}
        apiStatus={apiStatus}
        language={language}
        onLanguageChange={setLanguage}
        voiceEnabled={voiceEnabled}
        onVoiceToggle={() => setVoiceEnabled((v) => !v)}
      />

      <main className="relative z-10 flex-1 overflow-y-auto scrollbar-premium">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 flex flex-col gap-5">

          <AnimatePresence mode="wait">
            {showWelcome && (
              <motion.div
                key="welcome"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <WelcomeCard onSuggest={handleSuggest} />
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} language={language} />
            ))}
          </AnimatePresence>

          <AnimatePresence>
            {loading && <TypingIndicator key="typing" />}
          </AnimatePresence>

          <div ref={bottomRef} className="h-1" />
        </div>
      </main>

      <ChatInput
        value={input}
        onChange={setInput}
        onSend={handleSend}
        loading={loading}
        language={language}
        voiceEnabled={voiceEnabled}
      />

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
