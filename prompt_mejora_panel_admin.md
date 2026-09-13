# Prompt: Mejoras de UX, Categorías, Imágenes y Ficha de Producto — Panel de Administración (OilSkin)

Copia y pega el siguiente bloque en tu asistente de código (Claude Code, Cursor, etc.) para ejecutar la mejora.

---

## Rol y contexto

Eres un desarrollador Full-Stack Python/Flask trabajando sobre **OilSkin**, una plataforma e-commerce de cosméticos construida con **Flask (Application Factory + Blueprints)**, **MySQL en Aiven Cloud** (vía PyMySQL/Flask-MySQLdb), **Jinja2**, **Tailwind CSS v4** (dark mode, acento dorado `#CEB06E`) + **Flowbite** para componentes interactivos, y **Bootstrap 5** como soporte legado.

El panel administrativo vive en el blueprint `admin_blueprint` (`src/routes/admin_routes.py`, prefijo `/admin`), protegido por `@require_admin` (`src/utils/auth_utils.py`), y se renderiza sobre `templates/admin/admin_layout.jinja` con las vistas:

- `dashboard_inventario.html` — gestión integral de stock, precios y productos (`crear_producto`, `editar_producto`, `ajustar_stock`, `eliminar_producto`)
- `dashboard_ventas.html` — reportes de pedidos, actualización de domicilios y tracking (`cambiar_estado_pedido`, `actualizar_domicilio_pedido`)
- `dashboard_usuarios.html` — control de usuarios y roles
- `dashboard_metricas.html` — KPIs y gráficos

La lógica de datos vive en `src/models/ModeloProductos.py` (catálogo, stock, detalle e imágenes) y `src/models/ModeloCategoria.py` (categorías, slugs y filtrado del catálogo), contra las tablas `producto` y `categoria` de `database/defiv.sql`. La navegación pública se arma con `src/utils/nav_helper.py`, que inyecta las categorías en `templates/components/tailwind/_navbar.html` y `templates/components/tailwind/_footer.html`. La ficha de producto es `templates/detalle.jinja`, servida por `get_product(id)` en `main_routes.py`.

## Objetivo

Mejorar cuatro áreas del panel de administración y su impacto en el sitio público, sin romper el patrón MVC/Blueprints ni el estilo visual Tailwind v4 existente:

1. Corregir el posicionamiento y comportamiento de los submenús/modales del panel admin.
2. Hacer la gestión de categorías completamente dinámica y escalable en navbar y footer.
3. Permitir modificar la imagen de presentación de cada producto desde el admin.
4. Rediseñar la página de detalle de producto para que sea más personalizable, con características editables desde el panel.

## Tareas específicas

### 1. Submenús y modales del panel admin (posición y movilidad)
- Revisar los modales/dropdowns de `dashboard_inventario.html` (editar producto, ajustar stock, eliminar producto) y `dashboard_ventas.html` (cambiar estado de pedido, actualizar domicilio/guía) para corregir: apertura fuera del viewport, superposición con el sidebar de `admin_layout.jinja`, scroll interno cuando el contenido excede la altura de pantalla, y z-index inconsistente entre modal, overlay y navbar.
- Estandarizar estos submenús como componentes reutilizables de Flowbite (modal/dropdown) dentro de `templates/components/`, en vez de mantenerlos duplicados en cada vista del admin.
- Verificar el comportamiento responsivo (mobile/tablet) del sidebar de `admin_layout.jinja` junto con la apertura de estos submenús, para que no se recorten ni queden inaccesibles en pantallas pequeñas.

### 2. Gestión de categorías escalable
- Añadir en `admin_routes.py` los endpoints faltantes de CRUD de categorías (`crear_categoria`, `editar_categoria`, `eliminar_categoria`) bajo `/admin/categorias`, siguiendo el mismo patrón `@require_admin` + formulario/CSRF que usa `inventario/crear`.
- Extender `ModeloCategoria.py` con los métodos correspondientes de inserción, actualización y borrado (o desactivación lógica) contra la tabla `categoria`, evitando duplicados de `nombre_categoria`/slug.
- Agregar una vista `dashboard_categorias.html` (o sección dentro de `dashboard_inventario.html`) donde el admin pueda crear, renombrar, reordenar y eliminar categorías libremente.
- Adaptar `nav_helper.py`, `_navbar.html` y `_footer.html` para que soporten un número grande de categorías sin romper el diseño: usar un dropdown con scroll interno o buscador en el navbar, y una agrupación tipo "ver todas" o columnas múltiples en el footer, en lugar de listar todas las categorías en línea.
- Asegurar que `show_category(category_name)` en `main_routes.py` siga funcionando igual para cualquier categoría nueva creada dinámicamente (sin rutas hardcodeadas por nombre de categoría).

### 3. Imagen de presentación editable por producto
- Confirmar en `database/defiv.sql` y `ModeloProductos.py` cómo se almacena actualmente la imagen de cada producto (columna en `producto` o tabla relacionada); si no existe una columna clara para la imagen principal, agregarla (p. ej. `imagen_producto`) y actualizar la migración/script SQL correspondiente.
- Extender `crear_producto()` y `editar_producto(id_producto)` en `admin_routes.py` para aceptar subida/reemplazo de imagen (multipart/form-data), reutilizando el patrón ya usado en `update_profile_images()` de `user_routes.py` (subida a disco, validación de tipo/tamaño, nombre único).
- Guardar las imágenes de producto en una carpeta dedicada dentro de `static/` (p. ej. `static/uploads/productos/`), sirviendo la ruta guardada desde `ModeloProductos.py`.
- Reflejar el cambio de imagen en `dashboard_inventario.html` (previsualización antes de guardar) y en las vistas públicas que consumen el catálogo (`index.jinja`, `category.jinja`, `detalle.jinja`).

### 4. Página de detalle de producto más personalizable
- Ampliar el modelo de datos de producto (tabla `producto` o una nueva tabla relacionada, p. ej. `producto_atributo`) para soportar características configurables por producto (ingredientes, modo de uso, beneficios, badges/etiquetas), en lugar de un único campo `descripcion` fijo.
- Añadir en `ModeloProductos.py` los métodos para leer/escribir estos atributos, y en `admin_routes.py`/`dashboard_inventario.html` un formulario (o sección dentro del modal de edición) donde el admin pueda agregar, editar y eliminar estas características por producto.
- Rediseñar `templates/detalle.jinja` para renderizar estos atributos de forma dinámica (secciones colapsables, tabs o bloques con estilo Tailwind v4/dorado), manteniendo la sección de "productos relacionados" ya existente.
- Asegurar que `get_product(id)` en `main_routes.py` cargue estos nuevos atributos junto con el resto del detalle del producto en una sola consulta parametrizada (o vista SQL adicional si el volumen de joins lo justifica).

## Restricciones técnicas
- Mantener el patrón Application Factory y la separación por Blueprints (`main`, `auth`, `user`, `admin`).
- Todas las consultas a MySQL deben seguir el patrón DAO parametrizado ya usado (sin concatenar SQL), protegido contra inyección SQL.
- Todo formulario de administración debe mantener protección CSRF (Flask-WTF) y el decorador `@require_admin`.
- Cualquier tabla o columna nueva debe reflejarse en `database/defiv.sql` y, si aplica, en las vistas de `vistas.sql` / `vistas_admin.sql`.
- Respetar la identidad visual Tailwind v4 (dark mode, dorado `#CEB06E`) y los componentes Flowbite ya utilizados; evitar introducir un framework CSS/JS nuevo.
- Las imágenes deben seguir el estándar `.webp` ya usado en el resto del proyecto para optimización de carga.

## Criterios de aceptación
- [ ] Ningún modal o submenú del panel admin se abre fuera de la pantalla ni queda bloqueado por el sidebar, en desktop y mobile.
- [ ] El admin puede crear, editar y eliminar categorías sin tocar código, y el navbar/footer siguen siendo usables con decenas de categorías (scroll, buscador o agrupación, no un listado infinito en línea).
- [ ] El admin puede reemplazar la imagen de presentación de cualquier producto desde `dashboard_inventario.html`, con previsualización antes de guardar.
- [ ] La ficha de producto (`detalle.jinja`) muestra características configurables por producto, editables desde el panel de administración sin modificar plantillas.
- [ ] No se rompen los flujos existentes de catálogo, carrito, checkout ni ventas al agregar estos cambios.
