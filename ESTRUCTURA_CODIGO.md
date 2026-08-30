# 📁 Estructura del Código del Proyecto - OilSkin

Este documento contiene un análisis detallado y la representación visual de la estructura del proyecto **OilSkin**, una plataforma e-commerce de productos dermatológicos y de cuidado facial y corporal desarrollada con **Python (Flask)**, **MySQL**, **Jinja2**, **Tailwind CSS** y **Bootstrap**.

---

## 📐 Análisis Arquitectónico

La aplicación sigue el patrón arquitectónico **MVC (Modelo-Vista-Controlador)** con **Application Factory** y **Flask Blueprints** para lograr una arquitectura modular, desacoplada y escalable.

### 🔑 Componentes Clave de la Arquitectura:

1. **Patrón Application Factory (`create_app`)**:
   - Definido en [`app.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/app.py). Inicializa la aplicación Flask, conecta el pool de MySQL, configura las políticas de seguridad de cookies y sesiones (CSRF con Flask-WTF, SameSite Lax, HttpOnly), configura `ProxyFix` para despliegues detrás de proxies inversos y registra los Blueprints.

2. **Capa de Controladores / Rutas (`src/routes/`)**:
   - Dividida en 4 Blueprints independientes:
     - [`main_routes.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/routes/main_routes.py): Catálogo de productos, filtrado por categorías, búsqueda, carrito de compras de sesión y proceso de checkout para usuarios invitados o registrados.
     - [`auth_routes.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/routes/auth_routes.py): Autenticación de usuarios (inicio de sesión, registro con hash seguro bcrypt y cierre de sesión).
     - [`user_routes.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/routes/user_routes.py): Perfil de usuario, actualización de datos personales, historial de pedidos, detalle de pedidos y checkout autenticado.
     - [`admin_routes.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/routes/admin_routes.py): Panel de control administrativo con dashboards de ventas, métricas, gestión de inventario/stock y administración de usuarios.

3. **Capa de Modelos y Datos (`src/models/` y `src/database/`)**:
   - Conexión y pooling administrados en [`db_mysql.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/database/db_mysql.py) mediante `Flask-MySQLdb` / `PyMySQL` con soporte SSL (Aiven Cloud o MySQL local).
   - Patrón DAO / Modelo para consultas SQL parametrizadas:
     - [`ModeloProductos.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/models/ModeloProductos.py): Catálogo, stock, detalle e imágenes de productos.
     - [`ModeloCategoria.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/models/ModeloCategoria.py): Categorías y filtrado del catálogo.
     - [`ModeloCarrito.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/models/ModeloCarrito.py): Gestión de elementos del carrito y cálculo de subtotales.
     - [`ModeloPedido.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/models/ModeloPedido.py): Creación y trazabilidad de pedidos, domicilios y detalles de compra.
     - [`ModeloUsuario.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/models/ModeloUsuario.py): Gestión de credenciales, hashing bcrypt, roles y datos de contacto.
     - [`ModeloAdmin.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/models/ModeloAdmin.py): Métricas de ventas, ingresos, control de inventario y gestión de usuarios.

4. **Capa de Servicios (`src/services/`)**:
   - [`facturacion_service.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/services/facturacion_service.py): Generación de facturas electrónicas, cálculo de impuestos/descuentos, códigos QR y exportación/renderizado de comprobantes de pago.

5. **Capa de Formularios y Validaciones (`src/forms/`)**:
   - [`auth_forms.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/forms/auth_forms.py): Formularios de inicio de sesión y registro de usuarios con validaciones de campos y protección CSRF mediante WTForms.

6. **Capa de Utilidades y Seguridad (`src/utils/`)**:
   - [`auth_utils.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/utils/auth_utils.py): Decoradores de control de acceso (`@login_required`, `@admin_required`).
   - [`nav_helper.py`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/src/utils/nav_helper.py): Funciones auxiliares de navegación y carga contextual de categorías en plantillas.

7. **Capa de Presentación / Vistas (`src/templates/` y `src/static/`)**:
   - Motor de plantillas **Jinja2** modularizado con layouts base (`layout.jinja`, `admin_layout.jinja`, `layout_boostrap.jinja`).
   - Componentes reutilizables para Navbar, Footer, elementos UI y modales.
   - Hojas de estilo procesadas con **Tailwind CSS v4** (`input.css` -> `style.css`) y componentes auxiliares de **Bootstrap 5**.

8. **Scripts de Base de Datos (`database/`)**:
   - [`defiv.sql`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/database/defiv.sql): Estructura de tablas, llaves foráneas y restricciones.
   - [`vistas.sql`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/database/vistas.sql): Vistas SQL para consultas del cliente.
   - [`vistas_admin.sql`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/database/vistas_admin.sql): Vistas SQL para reportes administrativos y analítica.
   - [`queries.sql`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/database/queries.sql): Consultas de prueba y mantenimiento.

---

## 🌳 Árbol de Estructura del Repositorio

```text
OilSkin - Official Repo/
├── .env                              # Variables de entorno locales (credenciales DB, secret key)
├── .env.example                      # Plantilla de variables de entorno requeridas
├── .gitignore                        # Archivos y carpetas ignoradas por Git
├── app.py                            # Punto de entrada principal (Application Factory Flask)
├── wsgi.py                           # Punto de entrada para servidores WSGI en producción (Gunicorn)
├── Procfile                          # Configuración de ejecución en plataformas Cloud (Heroku/Render)
├── package.json                      # Scripts y dependencias de Frontend (Tailwind CSS CLI, Flowbite)
├── package-lock.json                 # Árbol de dependencias bloqueadas de Node.js
├── tailwind.config.js                # Configuración de Tailwind CSS
├── requirements.txt                  # Dependencias de Python / Flask
├── README.md                         # Documentación general y guía de instalación
├── ESTRUCTURA_CODIGO.md              # Documentación detallada de la arquitectura del proyecto
├── tmp_checkout_test.py              # Script auxiliar para pruebas del flujo de checkout
│
├── database/                         # Scripts SQL de inicialización y vistas
│   ├── defiv.sql                     # Creación de tablas base (rol, usuario, producto, pedido, factura, domicilio)
│   ├── queries.sql                   # Consultas de prueba y utilidades SQL
│   ├── vistas.sql                    # Vistas de base de datos para catálogo y clientes
│   └── vistas_admin.sql              # Vistas para métricas, inventario y ventas administrativas
│
├── static/                           # Directorio estático raíz / almacenamiento de uploads
│   └── uploads/                      # Almacenamiento de comprobantes e imágenes subidas
│
└── src/                              # Código fuente modularizado de la aplicación
    ├── __init__.py
    │
    ├── database/                     # Conector y pool de base de datos
    │   ├── __init__.py
    │   └── db_mysql.py               # Inicialización de Flask-MySQLdb y soporte SSL
    │
    ├── forms/                        # Formularios Flask-WTF
    │   ├── __init__.py
    │   └── auth_forms.py             # Formularios de Login y Registro con validadores
    │
    ├── models/                       # Modelos de datos y consultas SQL (Data Access Objects)
    │   ├── __init__.py
    │   ├── ModeloAdmin.py            # Métricas, reportes y gestión de inventario/usuarios
    │   ├── ModeloCarrito.py          # Operaciones del carrito de compras
    │   ├── ModeloCategoria.py        # Consultas de categorías y filtros
    │   ├── ModeloPedido.py           # Creación, consulta y actualización de órdenes
    │   ├── ModeloProductos.py        # Catálogo, detalles y gestión de stock de productos
    │   └── ModeloUsuario.py          # Gestión de cuentas, contraseñas con bcrypt y roles
    │
    ├── routes/                       # Enrutadores (Flask Blueprints)
    │   ├── __init__.py
    │   ├── admin_routes.py           # Blueprint `/admin` (dashboards, ventas, métricas, inventario)
    │   ├── auth_routes.py            # Blueprint `/auth` (login, register, logout)
    │   ├── main_routes.py            # Blueprint `/` (catálogo, detalle, carrito, checkout, sobre nosotros)
    │   └── user_routes.py            # Blueprint `/usuario` (perfil, pedidos, checkout autenticado)
    │
    ├── services/                     # Servicios y lógica de negocio
    │   ├── __init__.py
    │   └── facturacion_service.py    # Generación y validación de facturas / QR
    │
    ├── static/                       # Recursos estáticos de la aplicación
    │   ├── css/
    │   │   └── style.css             # Hoja de estilos compilada por Tailwind CSS
    │   ├── img/                      # Logotipos, banners e imágenes de marca
    │   ├── src_css/
    │   │   └── input.css             # Archivo fuente con directivas de Tailwind CSS
    │   └── uploads/                  # Carpeta de subida de archivos estáticos
    │
    ├── templates/                    # Plantillas Jinja2
    │   ├── carrito.jinja             # Vista interactiva del carrito de compras
    │   ├── category.jinja            # Catálogo filtrado por categoría
    │   ├── checkout.jinja            # Pasarela y formulario de finalización de compra
    │   ├── detalle.jinja             # Ficha técnica y detalle del producto
    │   ├── error_page.jinja          # Manejador visual de errores HTTP (404/500)
    │   ├── factura.html              # Plantilla para renderizado y descarga de factura
    │   ├── index.jinja               # Página de inicio / catálogo principal
    │   ├── sobre_nosotros.jinja      # Sección informativa corporativa
    │   ├── ver_factura.html          # Vista previa del comprobante de compra
    │   │
    │   ├── admin/                    # Vistas del panel de administración
    │   │   ├── admin_layout.jinja    # Layout base con sidebar para el administrador
    │   │   ├── dashboard_inventario.html # Gestión y control de stock de productos
    │   │   ├── dashboard_metricas.html   # Gráficos y KPIs de rendimiento
    │   │   ├── dashboard_usuarios.html   # Listado y gestión de usuarios y roles
    │   │   └── dashboard_ventas.html     # Reportes y detalle de órdenes de venta
    │   │
    │   ├── auth/                     # Vistas de autenticación
    │   │   ├── login.jinja           # Formulario de inicio de sesión
    │   │   └── register.jinja        # Formulario de registro de nuevos clientes
    │   │
    │   ├── components/               # Componentes modulares y parciales
    │   │   ├── boostrap/             # Layouts y componentes basados en Bootstrap 5
    │   │   │   ├── _footer_boostrap.html
    │   │   │   ├── _head_boostrap.jinja
    │   │   │   ├── _navbar_boostrap.html
    │   │   │   └── layout_boostrap.jinja
    │   │   └── tailwind/             # Layouts y componentes basados en Tailwind CSS
    │   │       ├── _footer.html
    │   │       ├── _head_utils.jinja
    │   │       ├── _navbar.html
    │   │       ├── layout.jinja
    │   │       ├── layout_profile.jinja
    │   │       └── elements/
    │   │           └── ui.jinja
    │   │
    │   └── profile/                  # Vistas del perfil del usuario
    │       ├── profile.html          # Información y edición de perfil del cliente
    │       ├── profile-cart.html     # Carrito guardado asociado al perfil
    │       ├── profile-checkout.html # Finalización de compra para usuarios autenticados
    │       └── profile-pedidos.html  # Historial y seguimiento de pedidos realizados
    │
    └── utils/                        # Módulos de apoyo y middleware
        ├── __init__.py
        ├── auth_utils.py             # Decoradores de autenticación y permisos
        └── nav_helper.py             # Inyección de categorías y enlaces en navegación
```

---

## 🛠️ Tecnologías y Dependencias Principales

### Backend & Seguridad:
- **Python 3.10+**: Lenguaje de programación base.
- **Flask (v3.1.3)**: Framework web WSGI ligero y modular.
- **Flask-MySQLdb (v2.0.0) / PyMySQL (v1.2.0) / mysqlclient (v2.2.8)**: Conectores a base de datos MySQL con soporte SSL para nubes como Aiven.
- **Flask-WTF (v1.3.0) & WTForms (v3.2.2)**: Formularios seguros con validación y protección CSRF.
- **Bcrypt (v5.0.0)**: Hashing seguro de contraseñas de usuarios.
- **python-decouple (v3.8) & python-dotenv (v1.2.2)**: Gestión y aislamiento de variables de entorno (`.env`).
- **Gunicorn (v26.2.0)**: Servidor HTTP WSGI para entornos de producción.
- **ReportLab (v5.0.0) & Pillow (v12.3.0) & QRCode (v8.2)**: Generación de facturas en PDF y códigos QR de trazabilidad.

### Frontend & UI:
- **Jinja2 (v3.1.6)**: Motor de plantillas del lado del servidor.
- **Tailwind CSS (v4.x)**: Framework CSS de utilidades modernas compilado mediante `@tailwindcss/cli`.
- **Flowbite (v4.0.1)**: Componentes interactivos basados en Tailwind CSS.
- **Bootstrap 5**: Utilizado en componentes específicos para soporte complementario.

---

## 🔗 Mapa de Rutas Principales

| Blueprint | Prefijo | Ruta | Método | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `main` | `/` | `/` | `GET` | Catálogo de productos / Landing page |
| `main` | `/` | `/categoria/<int:id>` | `GET` | Filtrado por categoría |
| `main` | `/` | `/producto/<int:id>` | `GET` | Detalle del producto |
| `main` | `/` | `/carrito` | `GET` | Vista del carrito de compras |
| `main` | `/` | `/carrito/agregar/<int:id>` | `POST` | Agregar producto al carrito |
| `main` | `/` | `/checkout` | `GET`, `POST` | Proceso de compra |
| `auth` | `/auth` | `/login` | `GET`, `POST` | Inicio de sesión |
| `auth` | `/auth` | `/register` | `GET`, `POST` | Registro de usuario |
| `auth` | `/auth` | `/logout` | `GET` | Cierre de sesión |
| `user` | `/usuario`| `/perfil` | `GET`, `POST` | Panel de datos del usuario |
| `user` | `/usuario`| `/pedidos` | `GET` | Historial de compras |
| `admin`| `/admin`| `/` | `GET` | Dashboard principal de métricas |
| `admin`| `/admin`| `/ventas` | `GET` | Reporte y gestión de ventas |
| `admin`| `/admin`| `/inventario` | `GET`, `POST` | Gestión de stock y catálogo |
| `admin`| `/admin`| `/usuarios` | `GET`, `POST` | Gestión de usuarios y permisos |
