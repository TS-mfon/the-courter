import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        court: {
          black: "#080708",
          panel: "#141014",
          gold: "#d6aa4f",
          crimson: "#9f2339",
          mist: "#e8dfcc"
        }
      },
      fontFamily: {
        serif: ["Georgia", "serif"]
      }
    }
  },
  plugins: []
};

export default config;
