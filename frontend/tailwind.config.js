/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#fdf5f3',
          100: '#fbe8e4',
          200: '#f9d5cd',
          300: '#f3b5a8',
          400: '#ea8c76',
          500: '#dc6b4f',
          600: '#c9523a',
          700: '#a8412d',
          800: '#8c3829',
          900: '#753327',
        },
        ts: {
          black: '#1A1A1A',
          white: '#FFFEFD',
          dark: '#1a1a2e',
          charcoal: '#2d2d3f',
          slate: '#3d3d54',
          muted: '#6b6b80',
        },
        stone: '#484848',
        dove: '#666666',
        sand: '#CCAC9F',
        pebble: '#EEE1DB',
        midnight: '#3E1768',
        aubergine: '#67295F',
        lilac: '#75457D',
        mauve: '#9F81A5',
        mist: '#C7C7E5',
        forest: '#025656',
        kelp: '#097270',
        coral: '#D45847',
      },
    },
  },
  plugins: [],
}
