/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/templates/**/*.{html,jinja,jinja2}",
    "!./src/templates/sena/**/*.html",
    "./src/static/js/**/*.js",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}