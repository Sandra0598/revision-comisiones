/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4fb",
          100: "#d6e4f5",
          600: "#1f4e78",
          700: "#163a5a",
        },
      },
      boxShadow: {
        soft: "0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.06)",
      },
    },
  },
  plugins: [],
};
