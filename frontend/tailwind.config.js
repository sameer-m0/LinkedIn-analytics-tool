/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#0a66c2", // LinkedIn blue
          dark: "#004182",
          light: "#e8f0fe",
        },
      },
    },
  },
  plugins: [],
};
