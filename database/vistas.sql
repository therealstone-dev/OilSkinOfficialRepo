CREATE OR REPLACE VIEW vw_historial_pedidos AS
SELECT 
    p.id_pedido,
    p.fecha_pedido,
    p.estado_pedido,
    p.subtotal AS pedido_subtotal,
    p.id_usuario,
    f.id_factura,
    f.subtotal AS factura_subtotal,
    f.total AS factura_total,
    f.metodo_pago,
    d.id_domicilio,
    d.direccion_entrega,
    d.ciudad,
    d.telefono_contacto,
    d.costo_envio,
    d.estado_envio,
    d.origen_despacho,
    d.lat_entrega,
    d.lng_entrega,
    d.lat_origen,
    d.lng_origen,
    d.empresa_envio,
    d.numero_guia,
    d.mensaje_transportista,
    d.fecha_estimada_entrega
FROM pedido p
LEFT JOIN factura f ON f.id_pedido = p.id_pedido
LEFT JOIN domicilio d ON d.id_pedido = p.id_pedido;

CREATE OR REPLACE VIEW vw_detalle_pedidos_productos AS
SELECT 
    dp.id_detalle,
    dp.id_pedido,
    dp.id_producto,
    dp.cantidad,
    dp.precio_unitario,
    dp.subtotal,
    pr.nombre_producto,
    pr.descripcion,
    pr.precio AS precio_catalogo
FROM detalle_pedido dp
JOIN producto pr ON pr.id_producto = dp.id_producto;

CREATE OR REPLACE VIEW vw_resumen_factura AS
SELECT 
    f.id_factura,
    f.id_pedido,
    f.fecha_factura,
    f.subtotal,
    f.total,
    f.metodo_pago,
    p.id_usuario,
    p.estado_pedido,
    u.nombre AS nombre_usuario,
    u.email AS email_usuario
FROM factura f
JOIN pedido p ON p.id_pedido = f.id_pedido
JOIN usuario u ON u.id_usuario = p.id_usuario;
