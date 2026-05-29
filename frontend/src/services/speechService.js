// ── Voice Input (Speech Recognition) ──────────────────────────────────────────
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

export const isSpeechInputSupported = () => !!SpeechRecognition;

export function createRecognition(langCode, onResult, onEnd, onError) {
  if (!SpeechRecognition) return null;
  const rec = new SpeechRecognition();
  rec.continuous = false;
  rec.interimResults = true;
  rec.lang = langCode === "en" ? "en-US"
           : langCode === "ta" ? "ta-IN"
           : langCode === "hi" ? "hi-IN"
           : langCode === "te" ? "te-IN"
           : langCode === "ml" ? "ml-IN"
           : "en-US";

  rec.onresult = (e) => {
    const transcript = Array.from(e.results)
      .map((r) => r[0].transcript)
      .join("");
    onResult(transcript, e.results[e.results.length - 1].isFinal);
  };
  rec.onend = onEnd;
  rec.onerror = (e) => onError(e.error);
  return rec;
}

// ── Text-to-Speech (Speech Synthesis) ─────────────────────────────────────────
export const isTTSSupported = () => !!window.speechSynthesis;

let currentUtterance = null;

export function speak(text, langCode, onEnd) {
  if (!window.speechSynthesis) return;
  stop();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = langCode === "en" ? "en-US"
             : langCode === "ta" ? "ta-IN"
             : langCode === "hi" ? "hi-IN"
             : langCode === "te" ? "te-IN"
             : langCode === "ml" ? "ml-IN"
             : "en-US";
  utter.rate = 0.95;
  utter.pitch = 1;
  if (onEnd) utter.onend = onEnd;
  currentUtterance = utter;
  window.speechSynthesis.speak(utter);
}

export function pause() {
  window.speechSynthesis?.pause();
}

export function resume() {
  window.speechSynthesis?.resume();
}

export function stop() {
  window.speechSynthesis?.cancel();
  currentUtterance = null;
}

export function isSpeaking() {
  return window.speechSynthesis?.speaking ?? false;
}
