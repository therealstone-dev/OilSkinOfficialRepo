# Prompt: Mejora de Geolocalización de Direcciones — Módulo de Seguimiento (OilSkin)

Copia y pega el siguiente bloque en tu asistente de código (Claude Code, Cursor, etc.) para ejecutar la mejora.

---

## Rol y contexto

Eres un desarrollador Full-Stack Python/Flask trabajando sobre **OilSkin**, una plataforma e-commerce de cosméticos construida con **Flask (Application Factory + Blueprints)**, **MySQL en Aiven Cloud** (vía PyMySQL/Flask-MySQLdb, SSL con `ca.pem`), **Jinja2**, **Tailwind CSS v4** (dark mode, acento dorado `#CEB06E`) y **Bootstrap 5** como soporte legado.

El proyecto ya cuenta con una tabla `domicilio` con soporte de geolocalización:

```
domicilio(id_domicilio, id_pedido, direccion_entrega, ciudad, telefono_contacto,
          costo_envio, estado_envio, origen_despacho,
          lat_entrega, lng_entrega, lat_origen, lng_origen,
          empresa_envio, numero_guia, mensaje_transportista, fecha_estimada_entrega)
```

Los puntos donde hoy se captura, guarda y muestra esta geolocalización son:

- **Checkout público** — `main_routes.py` → `checkout()` → `templates/checkout.jinja`
- **Checkout autenticado** — `user_routes.py` → `user_checkout()` → `templates/profile/profile-checkout.html`
- **Persistencia** — `src/models/ModeloPedido.py` (creación y trazabilidad de domicilios)
- **Seguimiento del cliente** — `user_routes.py` → `user_history()` → `templates/profile/profile-pedidos.html`, apoyado en la vista SQL `vw_historial_pedidos`
- **Gestión administrativa** — `admin_routes.py` → `actualizar_domicilio_pedido(id_pedido)` → `templates/admin/dashboard_ventas.html`

## Problema a resolver

Actualmente la geolocalización depende de coordenadas capturadas de forma manual o vía `navigator.geolocation` del navegador, sin validar la dirección de texto contra un servicio de geocodificación. Esto produce:

- Direcciones incompletas o ambiguas (`direccion_entrega` libre, sin normalizar).
- Coordenadas `lat_entrega` / `lng_entrega` vacías, nulas o desincronizadas con la ciudad indicada.
- Ausencia de visualización en mapa tanto en el checkout como en el seguimiento del pedido (`profile-pedidos.html`, `dashboard_ventas.html`), mostrando solo texto plano.
- Sin mecanismo de corrección cuando el administrador actualiza el domicilio de envío (`actualizar_domicilio_pedido`), las coordenadas no se recalculan.

## Objetivo

Implementar geocodificación (directa e inversa), autocompletado de direcciones y visualización en mapa, integrados en el flujo de checkout, el módulo de seguimiento del cliente y el panel administrativo, manteniendo la arquitectura MVC/Blueprints existente.

## Tareas específicas

### 1. Backend — Servicio de geocodificación
- Crear `src/services/geolocalizacion_service.py` con funciones `geocodificar_direccion(direccion, ciudad)` y `geocodificar_inverso(lat, lng)`, usando un proveedor de geocodificación (Google Maps Geocoding API, Mapbox o Nominatim/OpenStreetMap — indicar cuál según disponibilidad de API key).
- Manejar timeouts, errores de la API y direcciones no encontradas devolviendo un resultado estructurado (`{lat, lng, direccion_normalizada, precision, error}`).
- Cachear resultados (por ejemplo en memoria o tabla auxiliar) para evitar llamadas repetidas a la API con la misma dirección.

### 2. Backend — Integración en el flujo de pedido
- En `checkout()` (`main_routes.py`) y `user_checkout()` (`user_routes.py`), antes de persistir el domicilio, validar/normalizar la dirección ingresada llamando al nuevo servicio y solo aceptar coordenadas dentro de un rango razonable respecto a `ciudad`.
- En `ModeloPedido.py`, extender el método de creación de domicilio para guardar `direccion_entrega` ya normalizada y un campo de precisión/confianza del geocode (evaluar si conviene una columna nueva, p. ej. `geocode_precision`, en `database/defiv.sql`).
- En `actualizar_domicilio_pedido()` (`admin_routes.py`), recalcular `lat_entrega`/`lng_entrega` automáticamente cuando el admin edite `direccion_entrega` o `ciudad`.

### 3. Frontend — Checkout con autocompletado
- En `checkout.jinja` y `profile-checkout.html`, sustituir el campo de dirección libre por un input con autocompletado (Google Places Autocomplete, Mapbox Geocoding widget, o equivalente libre), consistente con el estilo Tailwind v4 dark/gold ya usado en el proyecto.
- Mantener como respaldo la geolocalización por navegador (`navigator.geolocation`) para cuando el usuario prefiera usar su ubicación actual, pero pasarla siempre por geocodificación inversa para obtener una dirección legible.

### 4. Frontend — Visualización en el seguimiento
- En `profile-pedidos.html` (seguimiento del cliente) y `dashboard_ventas.html` (panel admin), añadir un mapa embebido (Leaflet.js con tiles OSM, o Mapbox GL) que muestre `lat_origen/lng_origen` → `lat_entrega/lng_entrega`, reutilizando los datos que ya expone `vw_historial_pedidos`.
- Mostrar en el mapa el estado del envío (`estado_envio`) y la fecha estimada (`fecha_estimada_entrega`) como overlay o tooltip.

### 5. Configuración y seguridad
- Añadir la API key del proveedor de geocodificación como variable de entorno (`.env` / `.env.example`), cargada con `python-decouple`, nunca hardcodeada.
- Documentar el nuevo requisito en `requirements.txt` (SDK del proveedor, si aplica) y en `README.md`.

### 6. Pruebas
- Agregar pruebas con `pytest` para el nuevo servicio de geocodificación (casos: dirección válida, dirección ambigua, fallo de API, dirección fuera de cobertura), siguiendo el patrón ya usado en `tmp_checkout_test.py`.

## Restricciones técnicas
- Mantener el patrón Application Factory y la separación por Blueprints (`main`, `auth`, `user`, `admin`).
- Todas las consultas a MySQL deben seguir el patrón DAO parametrizado ya usado (sin concatenar SQL).
- No romper la compatibilidad con las vistas SQL existentes (`vw_historial_pedidos`, `vw_resumen_factura`); si se agregan columnas, actualizar las vistas correspondientes en `vistas.sql`.
- Respetar la identidad visual Tailwind v4 (dark mode, dorado `#CEB06E`) en cualquier componente nuevo de mapa o autocompletado.

## Criterios de aceptación
- [ ] Toda dirección guardada en `domicilio` queda normalizada y con coordenadas válidas (o un estado explícito de error si no se pudo geocodificar).
- [ ] El checkout público y el autenticado ofrecen autocompletado de direcciones.
- [ ] El cliente puede ver un mapa con el trayecto de su pedido en `/usuario/historial`.
- [ ] El admin puede corregir una dirección desde `dashboard_ventas.html` y las coordenadas se actualizan automáticamente.
- [ ] Las claves de API están en variables de entorno y documentadas en `.env.example`.
- [ ] Existen pruebas automatizadas para el nuevo servicio de geocodificación.
