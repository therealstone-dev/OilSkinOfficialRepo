import mysql.connector
from mysql.connector import Error
from tabulate import tabulate
import os
import sys
import csv

from decouple import config

# ==============================================================================
# CONFIGURACIÓN DE CONEXIÓN AIVEN MYSQL (LEÍDA DE VARIABLES DE ENTORNO)
# ==============================================================================
DB_CONFIG = {
    'host': config('MYSQL_HOST', default='localhost'),  
    'port': int(config('MYSQL_PORT', default='3306')),                               
    'user': config('MYSQL_USER', default='root'),                         
    'password': config('MYSQL_PASSWORD', default=''),             
    'database': config('MYSQL_DB', default='defaultdb'),                    
    'ssl_ca': config('MYSQL_SSL_CA', default='ca.pem'),          # Certificado de autoridad
    'ssl_verify_cert': True      # Validación estricta del servidor
}

def conectar_db():
    """Establece la conexión cifrada con MySQL usando solo ca.pem."""
    if not os.path.exists(DB_CONFIG['ssl_ca']):
        print(f"\n❌ ERROR: No se encontró el archivo '{DB_CONFIG['ssl_ca']}'.")
        sys.exit(1)

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"\n❌ Error al conectar a MySQL: {e}")
        sys.exit(1)

def obtener_tablas(connection):
    """Lista todas las tablas de la base de datos."""
    cursor = connection.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        ORDER BY table_name;
    """, (DB_CONFIG['database'],))
    tablas = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tablas

def ver_contenido_tabla(connection, nombre_tabla, limite=25):
    """Muestra el contenido de una tabla."""
    cursor = connection.cursor()
    try:
        cursor.execute(f"DESCRIBE `{nombre_tabla}`;")
        columnas = [col[0] for col in cursor.fetchall()]

        cursor.execute(f"SELECT * FROM `{nombre_tabla}` LIMIT %s;", (limite,))
        filas = cursor.fetchall()

        print(f"\n📋 Tabla '{nombre_tabla}' (Primeros {limite} registros):")
        if filas:
            print(tabulate(filas, headers=columnas, tablefmt="psql"))
        else:
            print("ℹ️ La tabla está vacía.")
    except Error as e:
        print(f"❌ Error al consultar la tabla: {e}")
    finally:
        cursor.close()

def buscar_en_tabla(connection, nombre_tabla):
    """OPCIÓN EXTRA 1: Busca un término en todas las columnas de la tabla."""
    termino = input("Introduce el texto o número a buscar: ")
    cursor = connection.cursor()
    try:
        cursor.execute(f"DESCRIBE `{nombre_tabla}`;")
        columnas = [col[0] for col in cursor.fetchall()]

        # Construimos un WHERE dinámico para buscar en cualquier columna
        condiciones = " OR ".join([f"`{col}` LIKE %s" for col in columnas])
        query = f"SELECT * FROM `{nombre_tabla}` WHERE {condiciones} LIMIT 20;"
        
        valores = [f"%{termino}%"] * len(columnas)
        cursor.execute(query, valores)
        filas = cursor.fetchall()

        if filas:
            print(f"\n🔍 Resultados encontrados para '{termino}':")
            print(tabulate(filas, headers=columnas, tablefmt="psql"))
        else:
            print(f"\nℹ️ No se encontró '{termino}' en la tabla {nombre_tabla}.")
    except Error as e:
        print(f"❌ Error en la búsqueda: {e}")
    finally:
        cursor.close()

def ejecutar_sql_libre(connection):
    """OPCIÓN EXTRA 2: Permite ejecutar consultas SQL personalizadas."""
    print("\n⚡ CONSOLA SQL (Escribe tu consulta y presiona Enter. Escribe 'salir' para cancelar)")
    query = input("mysql> ").strip()
    
    if query.lower() == 'salir' or not query:
        return

    cursor = connection.cursor()
    try:
        cursor.execute(query)
        if query.upper().startswith("SELECT"):
            columnas = [desc[0] for desc in cursor.description]
            filas = cursor.fetchall()
            if filas:
                print(tabulate(filas, headers=columnas, tablefmt="psql"))
            else:
                print("ℹ️ La consulta no devolvió resultados.")
        else:
            # Para INSERT, UPDATE, DELETE
            connection.commit()
            print(f"✅ Consulta ejecutada. Filas afectadas: {cursor.rowcount}")
    except Error as e:
        print(f"❌ Error de SQL: {e}")
    finally:
        cursor.close()

def exportar_csv(connection, nombre_tabla):
    """OPCIÓN EXTRA 3: Exporta el contenido de una tabla a un archivo CSV."""
    cursor = connection.cursor()
    try:
        cursor.execute(f"DESCRIBE `{nombre_tabla}`;")
        columnas = [col[0] for col in cursor.fetchall()]
        
        cursor.execute(f"SELECT * FROM `{nombre_tabla}`;")
        filas = cursor.fetchall()

        nombre_archivo = f"export_{nombre_tabla}.csv"
        with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo_csv:
            escritor = csv.writer(archivo_csv)
            escritor.writerow(columnas)
            escritor.writerows(filas)
            
        print(f"\n💾 ¡Éxito! Datos exportados a '{nombre_archivo}'.")
    except Error as e:
        print(f"❌ Error al exportar: {e}")
    except Exception as e:
        print(f"❌ Error de archivo: {e}")
    finally:
        cursor.close()

def main():
    print("🔌 Conectando a Aiven MySQL usando SSL (ca.pem)...")
    conn = conectar_db()
    
    if not conn:
        return

    print("✅ ¡Conexión segura establecida exitosamente!\n")

    try:
        while True:
            tablas = obtener_tablas(conn)
            
            print("\n" + "="*50)
            print(" 🛠️  EXPLORADOR AVANZADO DE BASE DE DATOS  🛠️ ")
            print("="*50)
            
            if not tablas:
                print("No se encontraron tablas.")
                break

            print("\nTablas disponibles:")
            for idx, tabla in enumerate(tablas, 1):
                print(f" [{idx}] {tabla}")

            print("\nOpciones Generales:")
            print("  • [S] Ejecutar consulta SQL libre")
            print("  • [R] Refrescar lista de tablas")
            print("  • [Q] Salir")
            
            opcion = input("\nElige una tabla (número) o una opción: ").strip()

            if opcion.lower() == 'q':
                break
            elif opcion.lower() == 'r':
                continue
            elif opcion.lower() == 's':
                ejecutar_sql_libre(conn)
            elif opcion.isdigit():
                idx = int(opcion) - 1
                if 0 <= idx < len(tablas):
                    tabla_seleccionada = tablas[idx]
                    
                    # Submenú para la tabla seleccionada
                    while True:
                        print(f"\n--- ACCIONES PARA TABLA: {tabla_seleccionada} ---")
                        print(" [1] Ver contenido (primeros 25)")
                        print(" [2] Buscar en la tabla")
                        print(" [3] Exportar a CSV")
                        print(" [4] Volver al menú principal")
                        
                        sub_opcion = input("Elige una acción: ").strip()
                        if sub_opcion == '1':
                            ver_contenido_tabla(conn, tabla_seleccionada)
                        elif sub_opcion == '2':
                            buscar_en_tabla(conn, tabla_seleccionada)
                        elif sub_opcion == '3':
                            exportar_csv(conn, tabla_seleccionada)
                        elif sub_opcion == '4':
                            break
                        else:
                            print("⚠️ Opción no válida.")
                else:
                    print("⚠️ Número fuera de rango.")
            else:
                print("⚠️ Opción no válida.")

    except Exception as e:
        print(f"\n⚠️ Ocurrió un error inesperado en la ejecución: {e}")

    finally:
        if 'conn' in locals() and conn and conn.is_connected():
            conn.close()
            print("\n👋 Conexión cerrada. ¡Hasta luego!")

if __name__ == "__main__":
    main()