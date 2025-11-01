/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brandNavy: '#000035',
        brandSlate: '#2E3B49',
        brandBlue: '#3065AC',
        navy: {
          900: '#0A1F44',
          800: '#0F2A5F',
          700: '#14367A',
        },
        gray: {
          900: '#0f1115',
          800: '#1a1d24',
          700: '#2a2f3a',
          600: '#3c4452',
          500: '#4b5563',
          400: '#9ca3af',
          300: '#d1d5db',
          200: '#e5e7eb',
          100: '#f3f4f6',
        }
      },
      boxShadow: {
        soft: '0 10px 30px rgba(0, 0, 0, 0.12)'
      }
    },
  },
  plugins: [],
}

