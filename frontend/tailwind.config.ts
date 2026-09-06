import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        scenic: {
          orange: "#FF7A00",
          "orange-bright": "#FF9533",
          "orange-deep": "#E56A00",
          black: "#0A0A0A",
          charcoal: "#121212",
        },
        adroit: {
          black: "#0A0A0A",
          charcoal: "#121212",
          card: "#121212",
          elevated: "#1A1A1A",
          border: "#2A2A2A",
          gold: "#FF7A00",
          "gold-bright": "#FF9533",
          "gold-deep": "#E56A00",
          cream: "#F6F1E8",
          muted: "#9A9A9A",
          white: "#FFFFFF",
        },
      },
      borderRadius: {
        widget: "24px",
        card: "14px",
        bubble: "18px",
      },
      boxShadow: {
        widget:
          "0 28px 80px rgba(0,0,0,0.58), 0 0 0 1px rgba(255,122,0,0.14)",
        gold: "0 8px 24px rgba(255,122,0,0.28)",
        header: "0 1px 0 rgba(255,255,255,0.04)",
        card: "0 10px 28px rgba(0,0,0,0.22)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        arabic: ["var(--font-cairo)", "Tahoma", "sans-serif"],
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "0% 50%" },
          "100%": { backgroundPosition: "100% 50%" },
        },
      },
      animation: {
        shimmer: "shimmer 2.4s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
