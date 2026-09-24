import os
import sys
import time
import statistics

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from src.database.db_mysql import get_connection

def run_benchmark():
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("          PRUEBA DE VELOCIDAD DE CONSULTAS SQL          ")
        print("=" * 60)

        # 1. Medir tiempo de conexión inicial (Handshake + SSL a Aiven)
        print("\n[1] Medición de tiempo de conexión (Handshake + SSL):")
        conn_times = []
        for i in range(5):
            t0 = time.perf_counter()
            conn = get_connection()
            t1 = time.perf_counter()
            conn_times.append((t1 - t0) * 1000)
            conn.close()
            print(f"  - Conexión #{i+1}: {conn_times[-1]:.2f} ms")

        avg_conn = statistics.mean(conn_times)
        print(f"  >>> Promedio de apertura de conexión: {avg_conn:.2f} ms\n")

        # 2. Medir consultas sobre una conexión activa (reutilizada)
        print("[2] Medición de consultas sobre conexión ya abierta:")
        conn = get_connection()
        cur = conn.cursor()

        queries = [
            ("Ping / SELECT 1", "SELECT 1"),
            ("Listar Categorías", "SELECT * FROM categoria"),
            ("Listar Productos Activos", "SELECT id_producto, nombre_producto, descripcion, precio, stock, imagenUrl, id_categoria, activo FROM producto WHERE activo = 1 ORDER BY nombre_producto ASC"),
            ("Obtener Producto Específico", "SELECT * FROM producto ORDER BY id_producto LIMIT 1"),
            ("Contar Usuarios", "SELECT COUNT(*) as total FROM usuario"),
            ("Últimos Pedidos", "SELECT * FROM pedido ORDER BY id_pedido DESC LIMIT 5")
        ]

        results = []

        for name, query in queries:
            times = []
            row_count = 0
            for _ in range(5):
                t0 = time.perf_counter()
                try:
                    cur.execute(query)
                    rows = cur.fetchall()
                    t1 = time.perf_counter()
                    times.append((t1 - t0) * 1000)
                    row_count = len(rows) if isinstance(rows, (list, tuple)) else 1
                except Exception as e:
                    print(f"  Error ejecutando '{name}': {e}")
                    times = [0]
                    break

            if times and times[0] > 0:
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                results.append({
                    "nombre": name,
                    "query": query,
                    "avg": avg_time,
                    "min": min_time,
                    "max": max_time,
                    "filas": row_count
                })

        cur.close()
        conn.close()

        # Mostrar tabla de resultados
        print(f"{'Consulta':<28} | {'Filas':<6} | {'Promedio':<10} | {'Mínimo':<10} | {'Máximo':<10}")
        print("-" * 72)
        for r in results:
            print(f"{r['nombre']:<28} | {r['filas']:<6} | {r['avg']:>7.2f} ms | {r['min']:>7.2f} ms | {r['max']:>7.2f} ms")

        # 3. Medir ciclo completo (conectar + consultar + cerrar) tal como ocurre en los endpoints actuales
        print("\n[3] Medición de ciclo completo (Conectar + SELECT + Cerrar - patrón actual de la app):")
        cycle_times = []
        for i in range(5):
            t0 = time.perf_counter()
            c = get_connection()
            cursor = c.cursor()
            cursor.execute("SELECT id_producto, nombre_producto, precio, stock FROM producto WHERE activo = 1")
            _ = cursor.fetchall()
            cursor.close()
            c.close()
            t1 = time.perf_counter()
            cycle_times.append((t1 - t0) * 1000)
            print(f"  - Ciclo completo #{i+1}: {cycle_times[-1]:.2f} ms")

        avg_cycle = statistics.mean(cycle_times)
        print(f"  >>> Promedio ciclo completo por petición: {avg_cycle:.2f} ms")

        return conn_times, results, cycle_times

if __name__ == '__main__':
    run_benchmark()
