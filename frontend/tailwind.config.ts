import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        adroit: {
          black: "#0B0B0B",
          card: "#111111",
          border: "#232323",
          gold: "#C8A24A",
          "gold-bright": "#F4E2A1",
          cream: "#F7F3E8",
          muted: "#A0A0A0",
          white: "#FFFFFF",
        },
      },
      boxShadow: {
        widget:
          "0 24px 80px rgba(0,0,0,0.55), 0 0 0 1px rgba(200,162,74,0.18)",
        gold: "0 10px 30px rgba(200,162,74,0.28)",
        header: "0 12px 40px rgba(0,0,0,0.35)",
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
