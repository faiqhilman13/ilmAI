/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9f4',
          100: '#d9f2e3',
          200: '#b5e4cb',
          300: '#84cfaa',
          400: '#51b383',
          500: '#2f9968',
          600: '#1f7a52',
          700: '#1a6244',
          800: '#174e38',
          900: '#14412f',
        },
        gold: {
          50: '#fdfaeb',
          100: '#faf1c7',
          200: '#f5e18b',
          300: '#efcb4f',
          400: '#e9b624',
          500: '#d99d13',
          600: '#bb780d',
          700: '#96560e',
          800: '#7c4413',
          900: '#693815',
        },
      },
      fontFamily: {
        arabic: ['Scheherazade New', 'Amiri', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
