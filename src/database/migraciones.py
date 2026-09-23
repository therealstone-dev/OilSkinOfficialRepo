"""
Módulo de migraciones automáticas e idempotentes para la base de datos MySQL de OilSkin.
Verifica y aplica cambios de esquema necesarios para OAuth 2.0 y OTP.
"""
from src.database.db_mysql import get_connection

def ejecutar_migraciones():
    """Ejecuta las migraciones necesarias para soportar Google OAuth y códigos OTP."""
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1. Modificar columnas de usuario para permitir registro OAuth sin contraseña/datos completos iniciales
        cur.execute("ALTER TABLE usuario MODIFY COLUMN contrasena VARCHAR(256) NULL")
        cur.execute("ALTER TABLE usuario MODIFY COLUMN direccion VARCHAR(150) NULL DEFAULT ''")
        cur.execute("ALTER TABLE usuario MODIFY COLUMN celular VARCHAR(20) NULL DEFAULT ''")

        # 2. Agregar google_id si no existe
        cur.execute("""
            SELECT COUNT(*) AS total 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuario' AND COLUMN_NAME = 'google_id'
        """)
        row = cur.fetchone()
        existe_google_id = row.get('total', 0) if isinstance(row, dict) else row[0]
        if not existe_google_id:
            cur.execute("ALTER TABLE usuario ADD COLUMN google_id VARCHAR(100) NULL UNIQUE")

        # 3. Agregar auth_provider si no existe
        cur.execute("""
            SELECT COUNT(*) AS total 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuario' AND COLUMN_NAME = 'auth_provider'
        """)
        row = cur.fetchone()
        existe_provider = row.get('total', 0) if isinstance(row, dict) else row[0]
        if not existe_provider:
            cur.execute("ALTER TABLE usuario ADD COLUMN auth_provider ENUM('local', 'google') DEFAULT 'local'")

        # 4. Crear tabla codigo_recuperacion para OTP de 6 dígitos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS codigo_recuperacion (
                id_codigo INT PRIMARY KEY AUTO_INCREMENT,
                id_usuario INT NOT NULL,
                codigo_hash VARCHAR(256) NOT NULL,
                expiracion DATETIME NOT NULL,
                intentos INT DEFAULT 0,
                utilizado TINYINT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE
            ) ENGINE=InnoDB
        """)

        conn.commit()
        return True, "Migraciones aplicadas exitosamente."
    except Exception as ex:
        if conn:
            conn.rollback()
        print(f"Error al ejecutar migraciones: {ex}")
        return False, str(ex)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    from app import app
    with app.app_context():
        ok, msg = ejecutar_migraciones()
        print(f"Resultado: {ok} - {msg}")
