/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
    "./app/**/*.py"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#f5f3ff',
          100: '#ede9fe',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
        }
      }
    },
  },
  safelist: [
    'hidden',
    'block',
    'flex',
    'grid',
    'opacity-50',
    'rotate-180',
    'day-mode',
    'animate-breathe',
    'animate-breathe-glow',
    'animate-float',
    'bg-gradient-to-r',
    'from-purple-600',
    'to-indigo-600',
    'text-white',
    'shadow-md',
    'shadow-purple-600/30',
    'text-slate-400',
    'hover:text-white',
    'hover:text-rose-300',
    'hover:underline',
    'text-rose-400',
    'text-purple-300',
    'bg-purple-600/20',
    'border-purple-500/30',
  ],
  plugins: [],
}
