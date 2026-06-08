/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/templates/**/*.{html,jinja,jinja2}",
    "!./src/templates/index.jinja",
    "./src/static/js/**/*.js",
    "!./src/templates/category.jinja",
    "!./src/templates/detalle.jinja",
    "!./src/templates/error_page.jinja",
    "!./src/templates/sobre_nosotros.jinja",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}