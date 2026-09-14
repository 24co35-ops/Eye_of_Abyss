import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Eye of Abyss design tokens (stitch-prompt.md Prompt 0)
        abyss: "#0D0B14",
        void: "#13111E",
        shadow: "#1C1929",
        mist: "#2A2640",
        gaze: {
          DEFAULT: "#F0A500",
          dim: "#7A5300",
          muted: "rgba(240, 165, 0, 0.12)",
        },
        signal: {
          DEFAULT: "#6B4FFF",
          dim: "#3D2E99",
          muted: "rgba(107, 79, 255, 0.12)",
        },
        threat: {
          DEFAULT: "#C92A2A",
          muted: "rgba(201, 42, 42, 0.12)",
        },
        safe: {
          DEFAULT: "#2A9D4E",
          muted: "rgba(42, 157, 78, 0.12)",
        },
        "text-primary": "#E8E6F2",
        "text-secondary": "#8884A8",
        "text-muted": "#4A4768",
      },
      fontFamily: {
        sans: ["Space Grotesk", "sans-serif"],
        display: ["Space Grotesk", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      width: {
        rail: "56px",
        context: "320px",
      },
      height: {
        topbar: "48px",
      },
      borderRadius: {
        DEFAULT: "4px",
        sm: "2px",
        md: "4px",
        lg: "4px",
        none: "0",
        full: "9999px",
      },
    },
  },
  plugins: [],
};

export default config;
