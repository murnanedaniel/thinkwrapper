/** @type {import('tailwindcss').Config} */
const colors = require('tailwindcss/colors');

module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Using very limited color palette - mostly grays
        primary: colors.gray,
        // Use just a hint of blue for rare accents (like focused inputs)
        accent: {
          500: '#4285F4', // Google blue for the rare accent (like focused inputs)
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      // Clean, minimal spacing
      spacing: {
        '128': '32rem',
      },
    },
  },
  plugins: [],
}

