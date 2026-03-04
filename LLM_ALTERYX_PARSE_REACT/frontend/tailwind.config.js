/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#12121a',
        card: '#1a1a28',
        border: '#2a2a3d',
        primary: '#00A650',        // BCG primary green
        'primary-dark': '#006C38', // BCG forest green
        secondary: '#6CC24A',      // BCG apple green
        accent: '#3D8B37',         // BCG mid green
        success: '#00A650',
        error: '#ef4444',
        warning: '#f59e0b',
        muted: '#94a3b8',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}

