/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        coal: { 50: '#f5f7f7', 100: '#e5ebeb', 600: '#3b5557', 700: '#294144', 800: '#1c3033', 900: '#102124' },
        minegreen: '#198754',
        mineamber: '#d9950b',
        minered: '#c94740',
      },
      boxShadow: { panel: '0 10px 24px rgba(20, 47, 48, 0.08)' },
    },
  },
  plugins: [],
}
