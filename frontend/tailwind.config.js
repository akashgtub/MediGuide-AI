/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        heading: ['"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
      },
      colors: {
        primary: {
          teal: '#0D9488',
          darkTeal: '#0F766E',
          navy: '#14213D',
          blue: '#2563EB',
        },
        teal: {
          50: '#F0FDFA',
          100: '#CCFBF1',
          200: '#99F6E4',
          300: '#5EEAD4',
          400: '#2DD4BF',
          500: '#14B8A6',
          600: '#0D9488', // Primary teal
          700: '#0F766E', // Dark teal
          800: '#115E59',
          900: '#134E4A',
          950: '#042F2E',
        },
        navy: {
          800: '#1B2A4A',
          900: '#14213D', // Deep navy
          950: '#0B132B', // Dark hero background
        },
        brand: {
          bg: '#F6F9FC',
          card: '#FFFFFF',
          text: '#172033',
          muted: '#64748B',
          border: '#E5EDF5',
        },
        accent: {
          success: '#10B981',
          warning: '#F59E0B',
          danger: '#EF4444',
          info: '#2563EB',
        }
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(20, 33, 61, 0.05), 0 1px 2px -1px rgba(20, 33, 61, 0.05)',
        'card-hover': '0 10px 25px -5px rgba(20, 33, 61, 0.08), 0 8px 10px -6px rgba(20, 33, 61, 0.04)',
        'glow-teal': '0 0 25px -5px rgba(13, 148, 136, 0.35)',
        'glow-blue': '0 0 25px -5px rgba(37, 99, 235, 0.35)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      }
    },
  },
  plugins: [],
}
