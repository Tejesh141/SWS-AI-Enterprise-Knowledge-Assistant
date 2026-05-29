import { SunIcon, MoonIcon, CpuChipIcon } from "@heroicons/react/24/outline";

export default function Header({ dark, onToggleDark, apiStatus }) {
  return (
    <header className="sticky top-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center shadow">
            <CpuChipIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-gray-900 dark:text-white leading-tight">
              SWS-AI Enterprise
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400 leading-tight">
              Knowledge Assistant
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800 text-xs font-medium">
            <span className={`w-2 h-2 rounded-full ${apiStatus === "online" ? "bg-emerald-500 animate-pulse" : "bg-red-500"}`} />
            <span className={apiStatus === "online" ? "text-emerald-600 dark:text-emerald-400" : "text-red-500"}>
              {apiStatus === "online" ? "API Online" : "API Offline"}
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-xs font-medium text-blue-700 dark:text-blue-300">
            <span>⚡</span><span>Gemini 2.0</span>
          </div>

          <button
            onClick={onToggleDark}
            className="w-9 h-9 rounded-lg flex items-center justify-center text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            {dark ? <SunIcon className="w-5 h-5" /> : <MoonIcon className="w-5 h-5" />}
          </button>
        </div>
      </div>
    </header>
  );
}
