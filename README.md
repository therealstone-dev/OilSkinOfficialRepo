# 🧴 OilSkin - Repositorio Oficial

Plataforma e-commerce para productos dermatológicos y de cuidado de la piel, desarrollada con **Python (Flask)**, **MySQL**, **Jinja2**, **Tailwind CSS** y **Bootstrap 5**.

---

## 📋 Requisitos Previos

Antes de comenzar con la instalación, asegúrate de tener instalado en tu sistema:

- **Python 3.10 o superior**: [Descargar Python](https://www.python.org/downloads/)
- **Node.js 18+ y npm** (opcional, para compilar estilos con Tailwind CSS): [Descargar Node.js](https://nodejs.org/)
- **Git**: [Descargar Git](https://git-scm.com/)
- **MySQL Server 8.0+** o una instancia gestionada en la nube (como [Aiven MySQL](https://aiven.io/)).

---

## 🚀 Guía de Instalación Paso a Paso

Sigue estos pasos para clonar, configurar y ejecutar el proyecto en tu entorno local:

### 1. Clonar el repositorio

Abre tu terminal y ejecuta:

```bash
git clone https://github.com/gracogamer3113-hash/oilskin-repo.git
cd "OilSkin - Official Repo"
```

---

### 2. Crear y activar el entorno virtual de Python

Se recomienda el uso de un entorno virtual para aislar las dependencias:

- **En Windows (PowerShell / CMD):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\activate
  ```

- **En Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

---

### 3. Instalar las dependencias de Python

Con el entorno virtual activo, instala los paquetes requeridos:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4. Instalar dependencias de Frontend y compilar Tailwind CSS (Opcional)

Si vas a modificar los estilos visuales en `src/static/src_css/input.css`:

```bash
# Instalar dependencias de Node.js
npm install

# Compilar estilos para producción (minificado)
npm run build

# O ejecutar el observador en modo desarrollo
npm run watch
```

---

### 5. Configuración de la Base de Datos MySQL

1. Conéctate a tu servidor MySQL o cliente preferido (MySQL Workbench, DBeaver, etc.).
2. Crea la base de datos (por ejemplo, `oilskin_db`):
   ```sql
   CREATE DATABASE oilskin_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   USE oilskin_db;
   ```
3. Ejecuta los scripts SQL ubicados en la carpeta [`database/`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/database):
   - **`database/defiv.sql`**: Crea las tablas principales (`rol`, `usuario`, `producto`, `categoria`, `pedido`, `factura`, `domicilio`, etc.).
   - **`database/vistas.sql`**: Genera las vistas para el catálogo y clientes.
   - **`database/vistas_admin.sql`**: Genera las vistas para reportes administrativos y métricas.

---

### 6. Configurar las Variables de Entorno

Copia el archivo [`.env.example`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/.env.example) y crea un nuevo archivo llamado `.env` en la raíz del proyecto:

```bash
# En Windows (PowerShell):
Copy-Item .env.example .env

# En Linux / Mac:
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales de conexión:

```ini
# Configuración de Base de Datos MySQL
MYSQL_HOST=localhost
MYSQL_USER=tu_usuario
MYSQL_PASSWORD=tu_contraseña
MYSQL_DB=oilskin_db
MYSQL_PORT=3306

# Ruta al certificado SSL (opcional para Aiven Cloud / dejar vacío si es MySQL local)
# MYSQL_SSL_CA=ca.pem

# Seguridad de Sesiones Flask
SECRET_KEY=tu_clave_secreta_super_segura
```

---

### 7. Ejecutar la Aplicación

#### Modo Desarrollo:
```bash
python app.py
```
Abre tu navegador en: [http://localhost:5000](http://localhost:5000)

#### Modo Producción con Gunicorn:
```bash
gunicorn wsgi:app --bind 0.0.0.0:5000 --workers 3
```

---

## 📂 Documentación del Proyecto

- Para consultar el análisis arquitectónico completo, la descripción de módulos y el mapa de rutas, revisa [`ESTRUCTURA_CODIGO.md`](file:///c:/Users/The%20Tilin%27t/Desktop/OilSkin%20-%20Official%20Repo/ESTRUCTURA_CODIGO.md).

---

## 🛠️ Scripts Útiles

| Comando | Descripción |
| :--- | :--- |
| `python app.py` | Inicia el servidor de desarrollo Flask en el puerto 5000 |
| `npm run build` | Compila y minifica los estilos de Tailwind CSS en `src/static/css/style.css` |
| `npm run watch` | Modo observador de Tailwind CSS para cambios en tiempo real |
| `pytest` | Ejecuta la suite de pruebas unitarias |
