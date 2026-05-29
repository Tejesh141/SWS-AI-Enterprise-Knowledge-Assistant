import { motion } from "framer-motion";

export default function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, x: -16, y: 8 }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      exit={{ opacity: 0, x: -16 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="flex items-start gap-3"
    >
      <motion.div
        animate={{ scale: [1, 1.1, 1] }}
        transition={{ duration: 1.5, repeat: Infinity }}
        className="w-9 h-9 rounded-2xl flex-shrink-0 flex items-center justify-center text-base shadow-brand"
        style={{ background: "linear-gradient(135deg, #5B21B6, #9333EA, #C084FC)" }}
      >
        🤖
      </motion.div>

      <div
        className="rounded-3xl rounded-tl-lg px-5 py-4 shadow-glass"
        style={{
          background: "rgba(255,255,255,0.82)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(168,85,247,0.15)",
        }}
      >
        <div className="flex items-center gap-2 mb-1.5">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              animate={{ scale: [0.4, 1, 0.4], opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.18, ease: "easeInOut" }}
              className="w-2 h-2 rounded-full"
              style={{ background: "linear-gradient(135deg, #7C3AED, #C084FC)" }}
            />
          ))}
        </div>
        <p className="text-xs text-brand-400 dark:text-brand-500 font-medium">
          Assistant is thinking…
        </p>
      </div>
    </motion.div>
  );
}
