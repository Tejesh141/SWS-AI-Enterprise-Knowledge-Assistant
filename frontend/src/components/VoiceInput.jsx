import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { createRecognition, isSpeechInputSupported } from "../services/speechService";

export default function VoiceInput({ language, onTranscript, disabled }) {
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const recRef = useRef(null);

  if (!isSpeechInputSupported()) return null;

  const start = () => {
    if (disabled || listening) return;
    const rec = createRecognition(
      language,
      (text, isFinal) => {
        setInterim(text);
        if (isFinal) { onTranscript(text); setInterim(""); }
      },
      () => setListening(false),
      () => setListening(false),
    );
    if (!rec) return;
    recRef.current = rec;
    rec.start();
    setListening(true);
  };

  const stop = () => {
    recRef.current?.stop();
    setListening(false);
    setInterim("");
  };

  return (
    <div className="relative flex items-center">
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={listening ? stop : start}
        disabled={disabled}
        title={listening ? "Stop listening" : "Voice input"}
        className="w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 disabled:opacity-40"
        style={
          listening
            ? { background: "linear-gradient(135deg,#EF4444,#F97316)", boxShadow: "0 0 20px rgba(239,68,68,0.4)" }
            : { background: "rgba(124,58,237,0.1)", border: "1px solid rgba(124,58,237,0.25)" }
        }
      >
        {listening ? (
          <motion.span
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 0.8, repeat: Infinity }}
            className="text-white text-sm"
          >
            🔴
          </motion.span>
        ) : (
          <span className="text-brand-600 dark:text-brand-400 text-sm">🎤</span>
        )}
      </motion.button>

      <AnimatePresence>
        {interim && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="absolute bottom-full mb-2 left-0 px-3 py-2 rounded-2xl text-xs text-brand-700 dark:text-brand-300 max-w-xs truncate"
            style={{ background: "rgba(168,85,247,0.12)", border: "1px solid rgba(168,85,247,0.25)", backdropFilter: "blur(8px)" }}
          >
            🎙️ {interim}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
