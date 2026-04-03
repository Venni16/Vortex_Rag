/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        carbon: "#050505",
        neon: {
          pink: "#ff00ff",
          cyan: "#00ffff",
          yellow: "#ffff00",
        },
        cyber: {
          grid: "rgba(0, 255, 255, 0.1)",
          glow: "0 0 10px rgba(0, 255, 255, 0.8)",
        }
      },
      fontFamily: {
        orbitron: ["Orbitron", "sans-serif"],
        mono: ["Space Mono", "monospace"],
      },
      animation: {
        'scanline': 'scanline 10s linear infinite',
        'pulse-neon': 'pulse-neon 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        'pulse-neon': {
          '0%, 100%': { opacity: 1, textShadow: '0 0 10px #00ffff' },
          '50%': { opacity: 0.8, textShadow: '0 0 20px #ff00ff' },
        }
      }
    },
  },
  plugins: [],
}
