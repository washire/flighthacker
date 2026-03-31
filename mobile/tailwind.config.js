/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#060D17",
          900: "#0D1B2A",
          800: "#142236",
          700: "#1B2D47",
          600: "#243A5E",
        },
        brand: {
          orange: "#F97316",
          teal: "#14B8A6",
        },
      },
    },
  },
};
