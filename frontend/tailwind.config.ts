import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080808",
        surface: {
          DEFAULT: "#111111",
          elevated: "#181818",
          card: "rgba(17, 17, 17, 0.8)",
          glass: "rgba(25, 25, 25, 0.65)",
          border: "rgba(255, 255, 255, 0.09)",
        },
        brand: {
          red: "#D92332",
          "red-glow": "#FF2B3D",
          "red-dark": "#8A0F1A",
          silver: "#F7F7F7",
          muted: "#B7B7B7",
          dim: "#666666",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "-apple-system", "sans-serif"],
        display: ["var(--font-syne)", "Cinzel", "Impact", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "fade-up": "fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "pulse-subtle": "pulseSubtle 3s ease-in-out infinite",
        "red-glow": "redGlow 4s ease-in-out infinite alternate",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(24px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSubtle: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
        redGlow: {
          "0%": { boxShadow: "0 0 25px -5px rgba(217, 35, 50, 0.3)" },
          "100%": { boxShadow: "0 0 45px 5px rgba(217, 35, 50, 0.6)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
