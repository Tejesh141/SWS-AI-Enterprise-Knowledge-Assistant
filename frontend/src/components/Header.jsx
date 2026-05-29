import { motion } from "framer-motion";
import { SunIcon, MoonIcon, SparklesIcon } from "@heroicons/react/24/outline";
import LanguageSelector from "./LanguageSelector";

export default function Header({
  dark, onToggleDark, apiStatus, language, onLanguageChange, voiceEnabled, onVoiceToggle,
}) {
  return (
    <motion.header
      initial={{ y: -64, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="sticky top-0 z-50"
    >
      {/* Glass backdrop */}
      <div className="glass dark:glass-dark border-b border-white/40 dark:border-brand-900/40 shadow-glass">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">

          {/* Logo + Title */}
          <div className="flex items-center gap-3 min-w-0">
            <motion.div
              whileHover={{ scale: 1.08, rotate: 5 }}
              whileTap={{ scale: 0.95 }}
              className="w-10 h-10 rounded-2xl flex-shrink-0 flex items-center justify-center shadow-brand"
              style={{ background: "linear-gradient(135deg, #5B21B6, #9333EA, #C084FC)" }}
            >
              <SparklesIcon className="w-5 h-5 text-white" />
            </motion.div>
            <div className="min-w-0">
              <h1 className="text-sm font-700 leading-tight text-gradient truncate">
                SWS AI Enterprise
              </h1>
              <p className="text-xs text-brand-600/70 dark:text-brand-300/60 leading-tight truncate">
                Knowledge Assistant
              </p>
            </div>
          </div>

          {/* Right controls */}
          <div className="flex items-center gap-2 flex-shrink-0">

            {/* API Status */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 }}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold"
              style={{
                background: apiStatus === "online"
                  ? "rgba(16,185,129,0.1)"
                  : "rgba(239,68,68,0.1)",
                border: `1px solid ${apiStatus === "online" ? "rgba(16,185,129,0.3)" : "rgba(239,68,68,0.3)"}`,
              }}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${apiStatus === "online" ? "bg-emerald-500 animate-pulse" : apiStatus === "offline" ? "bg-red-500" : "bg-amber-400 animate-pulse"}`}
              />
              <span className={apiStatus === "online" ? "text-emerald-600 dark:text-emerald-400" : apiStatus === "offline" ? "text-red-500" : "text-amber-500"}>
                {apiStatus === "online" ? "Live" : apiStatus === "offline" ? "Offline" : "Checking"}
              </span>
            </motion.div>

            {/* Gemini badge */}
            <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold"
              style={{ background: "rgba(124,58,237,0.1)", border: "1px solid rgba(124,58,237,0.25)", color: "#7C3AED" }}>
              <SparklesIcon className="w-3 h-3" />
              <span className="dark:text-brand-300">Gemini</span>
            </div>

            {/* Language Selector */}
            <LanguageSelector value={language} onChange={onLanguageChange} />

            {/* Voice toggle */}
            <motion.button
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.92 }}
              onClick={onVoiceToggle}
              title={voiceEnabled ? "Disable voice" : "Enable voice"}
              className={`w-9 h-9 rounded-xl flex items-center justify-center text-sm transition-all duration-200 ${
                voiceEnabled
                  ? "shadow-brand text-white"
                  : "text-brand-500 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-900/30"
              }`}
              style={voiceEnabled ? { background: "linear-gradient(135deg,#7C3AED,#A855F7)" } : {}}
            >
              {voiceEnabled ? "🎙️" : "🎤"}
            </motion.button>

            {/* Dark mode */}
            <motion.button
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.92 }}
              onClick={onToggleDark}
              className="w-9 h-9 rounded-xl flex items-center justify-center text-brand-500 dark:text-brand-300 hover:bg-brand-50 dark:hover:bg-brand-900/30 transition-all duration-200"
            >
              {dark
                ? <SunIcon className="w-5 h-5" />
                : <MoonIcon className="w-5 h-5" />}
            </motion.button>
          </div>
        </div>
      </div>
    </motion.header>
  );
}
