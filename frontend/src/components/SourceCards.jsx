import { motion } from "framer-motion";
import { DocumentTextIcon } from "@heroicons/react/24/outline";

export default function SourceCards({ sources }) {
  if (!sources?.length) return null;
  return (
    <div className="mt-4 pt-4 border-t border-brand-100/50 dark:border-brand-900/40">
      <p className="text-xs font-700 text-brand-500 dark:text-brand-400 uppercase tracking-widest mb-2.5 flex items-center gap-1.5">
        <DocumentTextIcon className="w-3.5 h-3.5" />
        Sources
      </p>
      <div className="flex flex-wrap gap-2">
        {sources.map((s, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.07, duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="flex items-center gap-2 px-3 py-2 rounded-2xl text-xs font-semibold"
            style={{
              background: "rgba(168,85,247,0.08)",
              border: "1px solid rgba(168,85,247,0.2)",
            }}
          >
            <span className="text-sm">📄</span>
            <span className="text-brand-700 dark:text-brand-300">{s.document}</span>
            <span
              className="px-1.5 py-0.5 rounded-full text-[10px] font-700"
              style={{ background: "rgba(124,58,237,0.15)", color: "#7C3AED" }}
            >
              p.{s.page}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
