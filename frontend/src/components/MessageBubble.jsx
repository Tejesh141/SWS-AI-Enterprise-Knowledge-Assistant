import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import SourceCards from "./SourceCards";
import SpeechControls from "./SpeechControls";

function ConfidenceBar({ score }) {
  const pct = Math.round(score * 100);
  const color = pct >= 80 ? "#10B981" : pct >= 60 ? "#F59E0B" : "#EF4444";
  const label = pct >= 80 ? "High" : pct >= 60 ? "Medium" : "Low";
  return (
    <div className="mt-3 pt-3 border-t border-brand-100/40 dark:border-brand-900/30">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs text-gray-400 dark:text-gray-500 font-medium">Confidence</span>
        <span className="text-xs font-700" style={{ color }}>{pct}% · {label}</span>
      </div>
      <div className="h-1 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
          className="h-full rounded-full"
          style={{ background: `linear-gradient(90deg, ${color}99, ${color})` }}
        />
      </div>
    </div>
  );
}

export default function MessageBubble({ message, language }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <motion.div
        initial={{ opacity: 0, x: 20, y: 8 }}
        animate={{ opacity: 1, x: 0, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        className="flex justify-end"
      >
        <div
          className="max-w-[78%] sm:max-w-[65%] px-5 py-3.5 rounded-3xl rounded-tr-lg text-white shadow-brand"
          style={{ background: "linear-gradient(135deg, #5B21B6, #7C3AED, #A855F7)" }}
        >
          <p className="text-sm leading-relaxed font-medium">{message.content}</p>
          <p className="text-xs text-brand-200/70 mt-1.5 text-right">{message.timestamp}</p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -20, y: 8 }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      className="flex items-start gap-3"
    >
      {/* Avatar */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, type: "spring", stiffness: 300 }}
        className="w-9 h-9 rounded-2xl flex-shrink-0 flex items-center justify-center text-base shadow-brand"
        style={{ background: "linear-gradient(135deg, #5B21B6, #9333EA, #C084FC)" }}
      >
        🤖
      </motion.div>

      {/* Bubble */}
      <div
        className="max-w-[85%] sm:max-w-[75%] rounded-3xl rounded-tl-lg px-5 py-4 shadow-glass"
        style={{
          background: "rgba(255,255,255,0.82)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(168,85,247,0.15)",
        }}
      >
        <div className="text-sm text-gray-800 dark:text-gray-100 leading-relaxed prose prose-sm max-w-none
          prose-p:my-1.5 prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0.5
          prose-headings:text-brand-800 prose-headings:font-700 prose-headings:my-2
          prose-strong:text-brand-700 prose-a:text-brand-600
          dark:prose-invert">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
        </div>

        {message.sources?.length > 0 && <SourceCards sources={message.sources} />}
        {message.confidence !== undefined && <ConfidenceBar score={message.confidence} />}

        <div className="flex items-center justify-between mt-2">
          <SpeechControls text={message.content} language={language} />
          <p className="text-xs text-gray-400 dark:text-gray-500">{message.timestamp}</p>
        </div>
      </div>
    </motion.div>
  );
}
