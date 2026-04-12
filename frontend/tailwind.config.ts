import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#6366f1",
        "primary-hover": "#4f46e5",
        "primary-dark": "#4338ca",
        bg: {
          primary: "#0a0a0a",
          secondary: "#111111",
          tertiary: "#161616",
          hover: "#1a1a1a",
        },
        text: {
          primary: "#fafafa",
          secondary: "#a1a1aa",
          muted: "#71717a",
        },
        border: {
          default: "#1f1f1f",
          hover: "#3f3f46",
          active: "#6366f1",
        },
      },
      fontFamily: {
        sans: [
          "Geist Sans",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        mono: ["Geist Mono", "Courier New", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
