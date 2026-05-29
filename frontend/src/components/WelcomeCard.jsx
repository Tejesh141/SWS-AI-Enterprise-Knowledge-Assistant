import { motion } from "framer-motion";
import { SparklesIcon } from "@heroicons/react/24/outline";

const TOPICS = [
  { label: "HR Policies",    question: "What are the HR policies at SWS AI?" },
  { label: "Leave Policies", question: "What is the annual leave policy?" },
  { label: "Benefits",       question: "What health insurance benefits do we have?" },
  { label: "Resignation",    question: "What is the notice period for resignation?" },
  { label: "WFH Guidelines", question: "What are the WFH guidelines?" },
  { label: "IT Security",    question: "What is the IT password policy?" },
  { label: "Procedures",     question: "What are the company procedures and code of conduct?" },
];

const SUGGESTIONS = [
  "What is the annual leave policy?",
  "How many sick leave days do I get?",
  "What is the notice period for resignation?",
  "What are the WFH guidelines?",
  "What health insurance benefits do we have?",
  "How does the performance review work?",
  "What tools does SWS AI use for communication?",
  "What is the IT password policy?",
];

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
};
const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } },
};

export default function WelcomeCard({ onSuggest }) {
  return (
    <motion.div variants={container} initial="hidden" animate="show" className="flex flex-col gap-5 py-4">

      {/* Hero card */}
      <motion.div
        variants={item}
        className="relative overflow-hidden rounded-4xl p-8 text-white shadow-brand-lg"
        style={{ background: "linear-gradient(135deg, #5B21B6 0%, #7C3AED 40%, #9333EA 70%, #A855F7 100%)" }}
      >
        {/* Decorative orbs */}
        <div className="absolute -top-12 -right-12 w-48 h-48 rounded-full opacity-20 animate-float"
          style={{ background: "radial-gradient(circle, #C084FC, transparent)" }} />
        <div className="absolute -bottom-8 -left-8 w-36 h-36 rounded-full opacity-15 animate-float"
          style={{ background: "radial-gradient(circle, #E9D5FF, transparent)", animationDelay: "2s" }} />

        <div className="relative z-10">
          <motion.div
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            className="w-14 h-14 rounded-3xl bg-white/20 backdrop-blur-sm flex items-center justify-center text-2xl mb-5"
          >
            🤖
          </motion.div>

          <h2 className="text-2xl sm:text-3xl font-bold leading-tight mb-2">
            Hi! I'm the SWS AI<br />
            <span className="text-purple-200">Enterprise Assistant</span>
          </h2>
          <p className="text-purple-200 text-sm sm:text-base mb-6 max-w-lg">
            Ask me anything about company policies, HR guidelines, IT security, or benefits.
          </p>

          {/* Topic pills — clickable, no emojis */}
          <div className="flex flex-wrap gap-2">
            {TOPICS.map((t) => (
              <motion.button
                key={t.label}
                whileHover={{ scale: 1.06, backgroundColor: "rgba(255,255,255,0.28)" }}
                whileTap={{ scale: 0.95 }}
                onClick={() => onSuggest(t.question)}
                className="px-3 py-1.5 rounded-full text-xs font-semibold text-white transition-all duration-150 cursor-pointer"
                style={{ background: "rgba(255,255,255,0.18)", border: "1px solid rgba(255,255,255,0.3)" }}
              >
                {t.label}
              </motion.button>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Suggested questions */}
      <motion.div variants={item}>
        <div className="flex items-center gap-2 mb-3">
          <SparklesIcon className="w-4 h-4 text-brand-500" />
          <p className="text-xs font-bold text-brand-600 dark:text-brand-400 uppercase tracking-widest">
            Suggested Questions
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((q) => (
            <motion.button
              key={q}
              variants={item}
              whileHover={{ scale: 1.04, y: -2 }}
              whileTap={{ scale: 0.96 }}
              onClick={() => onSuggest(q)}
              className="chip"
            >
              {q}
            </motion.button>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
