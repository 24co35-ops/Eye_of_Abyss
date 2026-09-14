import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Eye of Abyss design tokens (from design-doc.md)
        abyss:   "#0D0B14",
        void:    "#13111E",
        shadow:  "#1C1929",
        mist:    "#2A2640",
        gaze:    "#F0A500",
        "gaze-dim": "#7A5300",
        signal:  "#6B4FFF",
        "signal-dim": "#3D2E99",
        threat:  "#C92A2A",
        safe:    "#2A9D4E",
        "text-primary":   "#E8E6F2",
        "text-secondary": "#8884A8",
        "text-muted":     "#4A4768",
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        mono:    ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        DEFAULT: "4px",
      },
    },
  },
  plugins: [],
};

export default config;
