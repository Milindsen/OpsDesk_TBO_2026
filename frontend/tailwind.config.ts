import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ops: {
          bg: '#0f172a', // slate-900
          sidebar: '#1e293b', // slate-800
          surface: '#ffffff',
          primary: '#4f46e5', // indigo-600
        },
      },
      animation: {
        'pulse-fast': 'pulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
} satisfies Config
