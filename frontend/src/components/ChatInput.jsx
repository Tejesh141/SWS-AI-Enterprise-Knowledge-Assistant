import { useRef } from "react";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";

export default function ChatInput({ value, onChange, onSend, loading }) {
  const ref = useRef(null);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 px-4 py-4">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-end gap-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl px-4 py-3 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all shadow-sm">
          <textarea
            ref={ref}
            rows={1}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask anything about company policies..."
            disabled={loading}
            className="flex-1 bg-transparent text-sm text-gray-800 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 resize-none outline-none leading-relaxed max-h-32 overflow-y-auto scrollbar-thin disabled:opacity-50"
            style={{ minHeight: "24px" }}
          />
          <button
            onClick={onSend}
            disabled={loading || !value.trim()}
            className="w-9 h-9 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 flex items-center justify-center text-white transition-all hover:scale-105 active:scale-95 disabled:scale-100 shadow flex-shrink-0"
          >
            <PaperAirplaneIcon className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-gray-400 dark:text-gray-500 text-center mt-2">
          Answers are grounded in company documents only · Press Enter to send
        </p>
      </div>
    </div>
  );
}
