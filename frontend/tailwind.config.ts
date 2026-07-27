import type { Config } from "tailwindcss";

// Tokens de marca zühma+ (de zuhma.com y del prototipo).
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          ink: "#26242b",       // carbón sidebar
          ink2: "#322f38",
          accent: "#f26152",     // coral Zuhma
          accent2: "#f7902e",    // naranja Zuhma
          soft: "#fdece6",       // durazno suave
        },
        data: {
          s1: "#2a78d6",
          s2: "#eb6834",
          s3: "#1baf7a",
        },
        state: {
          good: "#1baf7a",
          warn: "#eda100",
          bad: "#e34948",
        },
        surface: "#ffffff",
        bg: "#f6f6fb",
        line: "#e9e8f0",
        ink: "#16151d",
        muted: "#6b6a7b",
        faint: "#9997a8",
      },
      borderRadius: {
        card: "16px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(20,18,40,.04),0 8px 24px rgba(20,18,40,.05)",
      },
    },
  },
  plugins: [],
};

export default config;
