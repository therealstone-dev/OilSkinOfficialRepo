-- Vistas MySQL para el Panel de Administración (Admin Dashboard)

-- 1. Vista de Desglose de Productos, Inventario y Ganancias
CREATE OR REPLACE VIEW vw_admin_inventario_ventas AS
SELECT 
    pr.id_producto,
    pr.nombre_producto,
    pr.precio AS precio_venta,
    pr.stock AS stock_actual,
    c.nombre_categoria,
    COALESCE(SUM(CASE WHEN p.estado_pedido != 'cancelado' THEN dp.cantidad ELSE 0 END), 0) AS unidades_vendidas,
    COALESCE(SUM(CASE WHEN p.estado_pedido != 'cancelado' THEN dp.subtotal ELSE 0 END), 0) AS ingresos_totales_producto,
    CASE 
        WHEN pr.stock <= 10 THEN 'Bajo Stock'
        WHEN pr.stock > 50 THEN 'Stock Abundante'
        ELSE 'Stock Normal'
    END AS estado_stock
FROM producto pr
LEFT JOIN categoria c ON c.id_categoria = pr.id_categoria
LEFT JOIN detalle_pedido dp ON dp.id_producto = pr.id_producto
LEFT JOIN pedido p ON p.id_pedido = dp.id_pedido
GROUP BY pr.id_producto, pr.nombre_producto, pr.precio, pr.stock, c.nombre_categoria;

-- 2. Vista de KPIs Generales de Administración
CREATE OR REPLACE VIEW vw_admin_resumen_kpis AS
SELECT 
    COUNT(DISTINCT CASE WHEN p.estado_pedido != 'cancelado' THEN p.id_pedido END) AS total_pedidos_completados,
    COALESCE(SUM(CASE WHEN p.estado_pedido != 'cancelado' THEN p.subtotal ELSE 0 END), 0) AS total_ingresos,
    COALESCE(AVG(CASE WHEN p.estado_pedido != 'cancelado' THEN p.subtotal END), 0) AS ticket_promedio
FROM pedido p;
