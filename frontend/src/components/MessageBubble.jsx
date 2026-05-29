import { DocumentTextIcon, CheckCircleIcon } from "@heroicons/react/24/outline";

function ConfidenceBar({ score }) {
  const pct = Math.round(score * 100);
  const color = pct >= 80 ? "bg-emerald-500" : pct >= 60 ? "bg-yellow-500" : "bg-red-400";
  return (
    <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">Confidence</span>
        <span className={`text-xs font-bold ${pct >= 80 ? "text-emerald-600" : pct >= 60 ? "text-yellow-600" : "text-red-500"}`}>
          {pct}%
        </span>
      </div>
      <div className="h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function SourceBadge({ source }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800">
      <DocumentTextIcon className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
      <div className="min-w-0">
        <p className="text-xs font-semibold text-blue-700 dark:text-blue-300 truncate">
          {source.document}
        </p>
        <p className="text-xs text-blue-500 dark:text-blue-400">Page {source.page}</p>
      </div>
      <CheckCircleIcon className="w-4 h-4 text-emerald-500 flex-shrink-0 ml-auto" />
    </div>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end animate-slide-up">
        <div className="max-w-[75%] px-4 py-3 rounded-2xl rounded-tr-sm bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-md">
          <p className="text-sm leading-relaxed">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 animate-slide-up">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center text-white text-sm flex-shrink-0 shadow">
        🤖
      </div>
      <div className="max-w-[80%] bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <p className="text-sm text-gray-800 dark:text-gray-100 leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>

        {message.sources?.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
              Sources
            </p>
            <div className="flex flex-col gap-2">
              {message.sources.map((s, i) => (
                <SourceBadge key={i} source={s} />
              ))}
            </div>
          </div>
        )}

        {message.confidence !== undefined && (
          <ConfidenceBar score={message.confidence} />
        )}

        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2 text-right">
          {message.timestamp}
        </p>
      </div>
    </div>
  );
}
