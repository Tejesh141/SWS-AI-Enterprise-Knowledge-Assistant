import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { XMarkIcon } from "@heroicons/react/24/outline";

const ICONS = {
  error:   { emoji: "⚠️", bg: "rgba(239,68,68,0.1)",   border: "rgba(239,68,68,0.3)",   text: "#EF4444" },
  success: { emoji: "✅", bg: "rgba(16,185,129,0.1)",  border: "rgba(16,185,129,0.3)",  text: "#10B981" },
  info:    { emoji: "ℹ️", bg: "rgba(124,58,237,0.1)",  border: "rgba(124,58,237,0.3)",  text: "#7C3AED" },
};

export function Toast({ toast, onDismiss }) {
  const style = ICONS[toast.type] ?? ICONS.info;

  useEffect(() => {
    const t = setTimeout(() => onDismiss(toast.id), toast.duration ?? 4000);
    return () => clearTimeout(t);
  }, [toast.id, toast.duration, onDismiss]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 24, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -16, scale: 0.9 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="flex items-start gap-3 px-4 py-3 rounded-2xl shadow-glass-lg max-w-sm w-full"
      style={{
        background: "rgba(255,255,255,0.95)",
        backdropFilter: "blur(20px)",
        border: `1px solid ${style.border}`,
      }}
    >
      <span className="text-base flex-shrink-0 mt-0.5">{style.emoji}</span>
      <div className="flex-1 min-w-0">
        {toast.title && (
          <p className="text-sm font-700 mb-0.5" style={{ color: style.text }}>{toast.title}</p>
        )}
        <p className="text-xs text-gray-600 leading-relaxed">{toast.message}</p>
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors"
      >
        <XMarkIcon className="w-3.5 h-3.5" />
      </button>
    </motion.div>
  );
}

export function ToastContainer({ toasts, onDismiss }) {
  return (
    <div className="fixed bottom-24 right-4 z-[100] flex flex-col gap-2 items-end">
      <AnimatePresence mode="popLayout">
        {toasts.map((t) => (
          <Toast key={t.id} toast={t} onDismiss={onDismiss} />
        ))}
      </AnimatePresence>
    </div>
  );
}
