/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/templates/**/*.{html,jinja,jinja2}",
    "!./src/templates/sena/**/*.html",
    "!./src/templates/index.jinja",
    "!./src/templates/sobre_nosotros.jinja",
    "!./src/templates/error_page.jinja",
    "!./src/templates/category.jinja",
    "!./src/templates/detalle.jinja",
    "./src/static/js/**/*.js",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}