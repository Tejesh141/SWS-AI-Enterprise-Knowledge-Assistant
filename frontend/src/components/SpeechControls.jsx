import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { speak, pause, resume, stop, isTTSSupported } from "../services/speechService";

export default function SpeechControls({ text, language }) {
  const [state, setState] = useState("idle"); // idle | playing | paused

  useEffect(() => () => stop(), []);

  if (!isTTSSupported()) return null;

  const handlePlay = () => {
    if (state === "idle") {
      speak(text, language, () => setState("idle"));
      setState("playing");
    } else if (state === "playing") {
      pause();
      setState("paused");
    } else {
      resume();
      setState("playing");
    }
  };

  const handleStop = () => {
    stop();
    setState("idle");
  };

  return (
    <div className="flex items-center gap-1 mt-2">
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={handlePlay}
        title={state === "idle" ? "Read aloud" : state === "playing" ? "Pause" : "Resume"}
        className="w-7 h-7 rounded-lg flex items-center justify-center text-xs transition-all duration-200 hover:bg-brand-50 dark:hover:bg-brand-900/30"
        style={state === "playing" ? { color: "#9333EA" } : { color: "#9CA3AF" }}
      >
        {state === "idle" ? "🔊" : state === "playing" ? "⏸️" : "▶️"}
      </motion.button>
      {state !== "idle" && (
        <motion.button
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={handleStop}
          title="Stop"
          className="w-7 h-7 rounded-lg flex items-center justify-center text-xs text-gray-400 hover:bg-brand-50 dark:hover:bg-brand-900/30 transition-all"
        >
          ⏹️
        </motion.button>
      )}
    </div>
  );
}
