/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Livvic", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50:  "#faf5ff",
          100: "#f3e8ff",
          200: "#e9d5ff",
          300: "#d8b4fe",
          400: "#c084fc",
          500: "#a855f7",
          600: "#9333ea",
          700: "#7c3aed",
          800: "#6d28d9",
          900: "#5b21b6",
          950: "#3b0764",
        },
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #5B21B6 0%, #7C3AED 35%, #9333EA 65%, #A855F7 100%)",
        "brand-gradient-soft": "linear-gradient(135deg, #7C3AED22 0%, #A855F722 100%)",
        "glass-gradient": "linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%)",
        "dark-glass": "linear-gradient(135deg, rgba(30,20,50,0.9) 0%, rgba(20,10,40,0.8) 100%)",
      },
      boxShadow: {
        "glass":    "0 8px 32px rgba(124,58,237,0.12), 0 2px 8px rgba(0,0,0,0.06)",
        "glass-lg": "0 20px 60px rgba(124,58,237,0.18), 0 4px 16px rgba(0,0,0,0.08)",
        "brand":    "0 8px 32px rgba(124,58,237,0.35)",
        "brand-lg": "0 16px 48px rgba(124,58,237,0.45)",
        "inner-glow": "inset 0 1px 0 rgba(255,255,255,0.15)",
      },
      animation: {
        "fade-in":     "fadeIn 0.4s ease-out",
        "slide-up":    "slideUp 0.4s cubic-bezier(0.16,1,0.3,1)",
        "slide-in-r":  "slideInRight 0.4s cubic-bezier(0.16,1,0.3,1)",
        "pulse-dot":   "pulseDot 1.4s infinite ease-in-out",
        "shimmer":     "shimmer 2s infinite linear",
        "float":       "float 6s ease-in-out infinite",
        "glow-pulse":  "glowPulse 2s ease-in-out infinite",
        "spin-slow":   "spin 8s linear infinite",
        "bounce-soft": "bounceSoft 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn:      { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp:     { from: { opacity: 0, transform: "translateY(16px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        slideInRight:{ from: { opacity: 0, transform: "translateX(16px)" }, to: { opacity: 1, transform: "translateX(0)" } },
        pulseDot:    { "0%,80%,100%": { transform: "scale(0.4)", opacity: 0.4 }, "40%": { transform: "scale(1)", opacity: 1 } },
        shimmer:     { from: { backgroundPosition: "-200% 0" }, to: { backgroundPosition: "200% 0" } },
        float:       { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-8px)" } },
        glowPulse:   { "0%,100%": { boxShadow: "0 0 20px rgba(168,85,247,0.4)" }, "50%": { boxShadow: "0 0 40px rgba(168,85,247,0.8)" } },
        bounceSoft:  { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-4px)" } },
      },
      backdropBlur: { xs: "2px" },
      borderRadius: { "2xl": "1rem", "3xl": "1.5rem", "4xl": "2rem" },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
