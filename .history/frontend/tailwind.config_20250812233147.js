/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          500: '#06b6d4',
          600: '#0891b2',
        },
        success: {
          400: '#4ade80',
          500: '#10b981',
          800: '#065f46',
          900: '#064e3b',
        },
        danger: {
          400: '#f87171',
          500: '#ef4444',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        warning: {
          500: '#f59e0b',
        },
        gray: {
          750: '#374151',
          850: '#1f2937',
        }
      }
    },
  },
  plugins: [],
}