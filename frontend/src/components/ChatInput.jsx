import { useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";
import VoiceInput from "./VoiceInput";

export default function ChatInput({ value, onChange, onSend, loading, language, voiceEnabled }) {
  const ref = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = "auto";
      ref.current.style.height = `${Math.min(ref.current.scrollHeight, 128)}px`;
    }
  }, [value]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSend(); }
  };

  return (
    <motion.div
      initial={{ y: 80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="sticky bottom-0 z-40"
    >
      <div
        className="border-t"
        style={{
          background: "rgba(250,247,255,0.92)",
          backdropFilter: "blur(24px)",
          borderColor: "rgba(168,85,247,0.15)",
        }}
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4">
          <div
            className="flex items-end gap-3 rounded-3xl px-4 py-3 transition-all duration-200"
            style={{
              background: "rgba(255,255,255,0.9)",
              backdropFilter: "blur(20px)",
              border: "1.5px solid rgba(168,85,247,0.2)",
              boxShadow: "0 4px 24px rgba(124,58,237,0.08)",
            }}
            onFocus={() => {}}
          >
            {/* Textarea */}
            <textarea
              ref={ref}
              rows={1}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask about policies, leave, benefits, security…"
              disabled={loading}
              className="flex-1 bg-transparent text-sm text-gray-800 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 resize-none outline-none leading-relaxed overflow-y-auto disabled:opacity-50 font-medium"
              style={{ minHeight: "24px", maxHeight: "128px" }}
            />

            {/* Voice input */}
            {voiceEnabled && (
              <VoiceInput
                language={language}
                onTranscript={(t) => onChange((prev) => (prev ? prev + " " + t : t))}
                disabled={loading}
              />
            )}

            {/* Send button */}
            <motion.button
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.92 }}
              onClick={onSend}
              disabled={loading || !value.trim()}
              className="w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 transition-all duration-200 disabled:opacity-40 disabled:scale-100"
              style={
                value.trim() && !loading
                  ? { background: "linear-gradient(135deg,#7C3AED,#A855F7)", boxShadow: "0 4px 16px rgba(124,58,237,0.4)" }
                  : { background: "rgba(156,163,175,0.3)" }
              }
            >
              {loading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                />
              ) : (
                <PaperAirplaneIcon className="w-4 h-4 text-white" />
              )}
            </motion.button>
          </div>

          <p className="text-xs text-center mt-2 text-gray-400 dark:text-gray-600">
            Answers grounded in company documents only · <kbd className="px-1 py-0.5 rounded text-[10px] bg-gray-100 dark:bg-gray-800">Enter</kbd> to send · <kbd className="px-1 py-0.5 rounded text-[10px] bg-gray-100 dark:bg-gray-800">Shift+Enter</kbd> for new line
          </p>
        </div>
      </div>
    </motion.div>
  );
}
