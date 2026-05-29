// MyMemory free translation API — no key required, 5000 chars/day free tier
const BASE = "https://api.mymemory.translated.net/get";

const cache = new Map();

async function translate(text, from, to) {
  if (from === to || !text.trim()) return text;
  const key = `${from}|${to}|${text}`;
  if (cache.has(key)) return cache.get(key);
  try {
    const url = `${BASE}?q=${encodeURIComponent(text)}&langpair=${from}|${to}`;
    const res = await fetch(url);
    const json = await res.json();
    const translated = json?.responseData?.translatedText ?? text;
    cache.set(key, translated);
    return translated;
  } catch {
    return text; // graceful fallback — return original on failure
  }
}

export const LANGUAGES = [
  { code: "en", label: "English",    flag: "🇬🇧" },
  { code: "ta", label: "Tamil",      flag: "🇮🇳" },
  { code: "hi", label: "Hindi",      flag: "🇮🇳" },
  { code: "te", label: "Telugu",     flag: "🇮🇳" },
  { code: "ml", label: "Malayalam",  flag: "🇮🇳" },
];

export const translateToEnglish = (text, fromLang) =>
  translate(text, fromLang, "en");

export const translateFromEnglish = (text, toLang) =>
  translate(text, "en", toLang);
