import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        moss: "#1877f2",
        fog: "#ffffff",
        paper: "#f8fafc",
        copper: "#0b5fcc",
        sand: "#94a3b8",
        sidebar: "#0b1220",
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "Segoe UI", "system-ui", "sans-serif"],
      },
      boxShadow: {
        panel: "0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 16px rgba(15, 23, 42, 0.04)",
      },
    },
  },
  plugins: [],
} satisfies Config;
