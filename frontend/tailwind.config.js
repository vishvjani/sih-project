/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          950: '#07080a',
          900: '#0c0d10',
          850: '#111317',
          800: '#16181e',
          750: '#1c1e26',
          700: '#232630',
          600: '#2e3240',
          border: 'rgba(255, 255, 255, 0.08)',
          'border-strong': 'rgba(255, 255, 255, 0.15)',
        },
        neon: {
          green: '#96E071',
          'green-glow': 'rgba(150, 224, 113, 0.25)',
          'green-bright': '#b3f595',
          darkgreen: '#1a3312',
          red: '#ff4d4d',
          'red-glow': 'rgba(255, 77, 77, 0.25)',
          cyan: '#38bdf8',
          yellow: '#facc15',
        },
        secondary: '#8F8F8F',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      animation: {
        'scan': 'scan 3s linear infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'laser': 'laser 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2.5s infinite linear',
        'ticker': 'ticker 30s linear infinite',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(0%)' },
          '50%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0%)' },
        },
        laser: {
          '0%, 100%': { transform: 'translateY(-100%)', opacity: 0 },
          '50%': { transform: 'translateY(100%)', opacity: 1 },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        ticker: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        }
      },
    },
  },
  plugins: [],
}
