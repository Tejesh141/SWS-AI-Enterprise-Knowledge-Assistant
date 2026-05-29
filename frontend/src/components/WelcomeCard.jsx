const SUGGESTIONS = [
  "What is the annual leave policy?",
  "How many sick leave days do employees get?",
  "What is the notice period for resignation?",
  "What are the WFH guidelines?",
  "What health insurance benefits do we have?",
  "What tools does SWS AI use for communication?",
  "What is the IT password policy?",
];

export default function WelcomeCard({ onSuggest }) {
  return (
    <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-2xl p-6 text-white shadow-lg">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-xl">
          🤖
        </div>
        <div>
          <p className="font-semibold text-sm">SWS AI Enterprise Assistant</p>
          <p className="text-blue-200 text-xs">Powered by Gemini + Company Knowledge Base</p>
        </div>
      </div>

      <p className="text-sm text-blue-100 mb-4">
        Hi! Ask me anything about company policies, HR guidelines, IT security, or benefits.
      </p>

      <p className="text-xs font-semibold text-blue-200 uppercase tracking-wider mb-3">
        Suggested Questions
      </p>
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => onSuggest(q)}
            className="px-3 py-1.5 rounded-full bg-white/15 hover:bg-white/25 text-xs font-medium text-white border border-white/20 transition-all hover:scale-105 active:scale-95"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
