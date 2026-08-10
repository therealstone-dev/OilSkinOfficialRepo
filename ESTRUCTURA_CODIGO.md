# 📁 Estructura del Código del Proyecto - OilSkin

Este documento contiene un análisis detallado y la representación visual de la estructura del proyecto **OilSkin**, una aplicación web e-commerce de productos dermatológicos y de cuidado de la piel desarrollada con **Python (Flask)**, **MySQL**, **Jinja2**, **Tailwind CSS** y **Bootstrap**.

---

## 📐 Análisis Arquitectónico

La aplicación sigue el patrón arquitectónico **MVC (Modelo-Vista-Controlador)** optimizado con la estrategia **Application Factory** y **Flask Blueprints** para lograr una arquitectura modular, escalable y mantenible.

### 🔑 Componentes Clave de la Arquitectura:

1. **Patrón Application Factory (`create_app`)**:
   - Definido en [app.py](file:///c:/Users/ESTUDIANTE/Desktop/oilskin/OilSkinOfficialRepo/app.py). Inicializa la aplicación Flask, configura la base de datos MySQL, establece políticas de seguridad de sesiones (CSRF, SameSite Lax, HttpOnly) y registra los Blueprints de enrutamiento.

2. **Capa de Controladores / Rutas (`src/routes/`)**:
   - La lógica de control está dividida en 4 Blueprints independientes:
     - `main_routes`: Manejo del catálogo público, vista de productos, categorías, carrito y checkout.
     - `auth_routes`: Gestión de autenticación (login, registro, logout).
     - `user_routes`: Perfil del usuario, historial de pedidos y compras.
     - `admin_routes`: Panel administrativo (métricas de ventas, inventario, gestión de usuarios).

3. **Capa de Modelos y Datos (`src/models/` y `src/database/`)**:
   - Conexión MySQL abstraída mediante `Flask-MySQLdb` / `mysqlclient` en `db_mysql.py`.
   - Modelos encargados de realizar las consultas SQL y encapsular la lógica de negocio (`ModeloProductos`, `ModeloUsuario`, `ModeloCarrito`, `ModeloPedido`, `ModeloAdmin`, `ModeloCategoria`).

4. **Capa de Servicios (`src/services/`)**:
   - Encapsula lógica compleja reutilizable, como `facturacion_service.py` para la generación de facturas y recibos.

5. **Capa de Presentación / Vistas (`src/templates/` y `src/static/`)**:
   - Vistas estructuradas con el motor de plantillas **Jinja2**.
   - Modularización mediante plantillas base (`layout.jinja`, `admin_layout.jinja`), layouts de Tailwind CSS y Bootstrap, y componentes reutilizables (`_navbar`, `_footer`).

6. **Pruebas y Base de Datos (`tests/` y `database/`)**:
   - Scripts SQL para la creación de tablas, vistas normales y de administración.
   - Suite de pruebas unitarias implementada con `pytest`.

---

## 🌳 Árbol de Estructura de Directorios

```text
oilskin/
├── ca.pem                                # Certificado SSL para conexión segura a MySQL
├── queries.sql                           # Consultas de prueba a nivel de workspace
├── usalotilin.py                         # Script de utilidad / migración auxiliar
├── ddfrsfed.html                         # Archivo HTML borrador / prueba
├── tests/                                # Suite de pruebas a nivel raíz
│   └── test_facturacion_service.py
└── OilSkinOfficialRepo/                  # Repositorio y código principal del proyecto
    ├── .env                              # Variables de entorno locales
    ├── .env.example                      # Plantilla de variables de entorno
    ├── .gitignore                        # Archivos ignorados en control de versiones
    ├── app.py                            # Punto de entrada principal (Application Factory)
    ├── package.json                      # Configuración de dependencias NPM (Tailwind CSS)
    ├── package-lock.json                 # Lockfile de dependencias NPM
    ├── tailwind.config.js                # Configuración del framework Tailwind CSS
    ├── requirements.txt                  # Dependencias de Python / Flask
    ├── README.md                         # Instrucciones de despliegue y uso
    ├── tmp_checkout_test.py              # Script de prueba temporal para flujo de checkout
    │
    ├── database/                         # Scripts SQL del sistema
    │   ├── defiv.sql                     # Definición de tablas e esquema principal
    │   ├── queries.sql                   # Consultas SQL reutilizables
    │   ├── vistas.sql                    # Vistas SQL para el lado del usuario/cliente
    │   └── vistas_admin.sql              # Vistas SQL avanzadas para reportes del admin
    │
    ├── src/                              # Código fuente modularizado de la aplicación
    │   ├── __init__.py
    │   │
    │   ├── database/                     # Configuración de base de datos
    │   │   ├── __init__.py
    │   │   └── db_mysql.py               # Inicialización y pool de conexiones MySQLdb
    │   │
    │   ├── forms/                        # Formularios Flask-WTF
    │   │   └── auth_forms.py             # Formularios de Login y Registro con validaciones
    │   │
    │   ├── models/                       # Modelos de acceso a datos (Patrón DAO/Model)
    │   │   ├── __init__.py
    │   │   ├── ModeloAdmin.py            # Operaciones administrativas y métricas
    │   │   ├── ModeloCarrito.py          # Lógica del carrito de compras
    │   │   ├── ModeloCategoria.py        # Consulta y filtrado por categorías
    │   │   ├── ModeloPedido.py           # Gestión y trazabilidad de órdenes
    │   │   ├── ModeloProductos.py        # Catálogo, inventario y detalles de productos
    │   │   └── ModeloUsuario.py          # Autenticación, usuarios y encriptación bcrypt
    │   │
    │   ├── routes/                       # Enrutadores (Flask Blueprints)
    │   │   ├── __init__.py
    │   │   ├── admin_routes.py           # Rutas del panel de administración (`/admin`)
    │   │   ├── auth_routes.py            # Rutas de login/registro/logout (`/auth`)
    │   │   ├── main_routes.py            # Rutas principales del comercio (`/`)
    │   │   └── user_routes.py            # Rutas del perfil del cliente (`/usuario`)
    │   │
    │   ├── services/                     # Lógica de negocio avanzada
    │   │   ├── __init__.py
    │   │   └── facturacion_service.py    # Servicio de cálculo e impresión de facturas
    │   │
    │   ├── static/                       # Recursos estáticos de la aplicación
    │   │   ├── css/
    │   │   │   └── style.css             # CSS compilado y estilos personalizados
    │   │   ├── img/                      # Logotipos, imágenes publicitarias y fondo
    │   │   └── src_css/
    │   │       └── input.css             # Directivas fuente de Tailwind CSS
    │   │
    │   ├── templates/                    # Plantillas Jinja2
    │   │   ├── carrito.jinja             # Vista del carrito de compras
    │   │   ├── category.jinja            # Vista de catálogo filtrado por categoría
    │   │   ├── checkout.jinja            # Vista de finalización de compra
    │   │   ├── detalle.jinja             # Detalle de producto individual
    │   │   ├── error_page.jinja          # Página personalizada de errores (404/500)
    │   │   ├── factura.html              # Plantilla para generación de factura
    │   │   ├── index.jinja               # Landing page / página de inicio
    │   │   ├── sobre_nosotros.jinja      # Sección informativa "Sobre Nosotros"
    │   │   ├── ver_factura.html          # Previsualización de comprobante de compra
    │   │   │
    │   │   ├── admin/                    # Vistas del Panel de Administración
    │   │   │   ├── admin_layout.jinja    # Layout base de administración
    │   │   │   ├── dashboard_inventario.html # Gestión de stock e inventario
    │   │   │   ├── dashboard_metricas.html   # Gráficos y métricas de desempeño
    │   │   │   ├── dashboard_usuarios.html   # Administración de usuarios registrados
    │   │   │   └── dashboard_ventas.html     # Reportes de ventas y pedidos
    │   │   │
    │   │   ├── auth/                     # Vistas de Autenticación
    │   │   │   ├── login.jinja           # Formulario de inicio de sesión
    │   │   │   └── register.jinja        # Formulario de registro de nuevo usuario
    │   │   │
    │   │   ├── components/               # Componentes web reutilizables
    │   │   │   ├── boostrap/             # Layouts y componentes con Bootstrap
    │   │   │   │   ├── layout_boostrap.jinja
    │   │   │   │   ├── _footer_boostrap.html
    │   │   │   │   ├── _head_boostrap.jinja
    │   │   │   │   └── _navbar_boostrap.html
    │   │   │   └── tailwind/             # Layouts y componentes con Tailwind
    │   │   │       ├── layout.jinja
    │   │   │       ├── layout_profile.jinja
    │   │   │       ├── _footer.html
    │   │   │       ├── _head_utils.jinja
    │   │   │       ├── _navbar.html
    │   │   │       └── elements/
    │   │   │           └── ui.jinja
    │   │   │
    │   │   └── profile/                  # Vistas del perfil del usuario cliente
    │   │       ├── profile.html          # Información personal del usuario
    │   │       ├── profile-cart.html     # Carrito guardado del perfil
    │   │       ├── profile-checkout.html # Proceso de pago desde el perfil
    │   │       └── profile-pedidos.html  # Historial de pedidos realizados
    │   │
    │   └── utils/                        # Funciones de ayuda e intermediarios
    │       ├── auth_utils.py             # Decoradores de protección de rutas y permisos
    │       └── nav_helper.py             # Carga dinámica de menú de navegación y categorías
    │
    └── tests/                            # Pruebas integradas dentro del paquete principal
        ├── test_admin_management.py      # Pruebas de funcionalidades administrativas
        └── test_facturacion_service.py   # Pruebas de servicio de facturación
```

---

## 🛠️ Tecnologías y Dependencias Principales

### Backend & Seguridad:
- **Python 3**: Lenguaje principal de programación.
- **Flask (v3.1.3)**: Framework web ligero.
- **Flask-MySQLdb (v2.0.0) / mysqlclient (v2.2.8)**: Conector de base de datos MySQL con soporte de pool de conexiones.
- **Flask-WTF (v1.1.1) & WTForms (v3.0.1)**: Creación y validación segura de formularios con protección CSRF.
- **Bcrypt (v4.0.1)**: Encriptación y hashing seguro de contraseñas de usuarios.
- **python-decouple (v3.8) & python-dotenv**: Gestión de variables de entorno seguras (`.env`).

### Frontend & UI:
- **Jinja2 (v3.1.6)**: Motor de plantillas servidor con herencia y macros.
- **Tailwind CSS**: Framework de utilidades CSS para diseño responsive moderno.
- **Bootstrap 5**: Utilizado en componentes específicos para maquetación rápida.

---

## 🚀 Guía de Inicio Rápido

1. **Crear entorno virtual de Python**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Linux/Mac
   .venv\Scripts\activate     # En Windows
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r OilSkinOfficialRepo/requirements.txt
   ```

3. **Configurar Variables de Entorno**:
   Crear archivo `.env` en `OilSkinOfficialRepo/` tomando como base `.env.example`:
   ```ini
   MYSQL_HOST=localhost
   MYSQL_USER=tu_usuario
   MYSQL_PASSWORD=tu_password
   MYSQL_DB=oilskin_db
   SECRET_KEY=clave_secreta_para_sesiones
   ```

4. **Ejecutar la Aplicación**:
   ```bash
   cd OilSkinOfficialRepo
   python app.py
   ```
   La aplicación estará disponible en `http://localhost:5000`.

---
*Documento generado automáticamente para documentar la arquitectura y estructura del repositorio OilSkin.*
