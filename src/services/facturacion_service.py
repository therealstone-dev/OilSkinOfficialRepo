from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from typing import Any, Dict, List, Optional

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.utils import ImageReader

from src.database.db_mysql import get_connection


class FacturacionService:
    """Servicio de facturación orientado a transacciones y aritmética decimal.

    El objetivo de este servicio es encapsular la lógica de negocio de facturación
    para que la ruta de checkout pueda delegar la generación de facturas sin duplicar
    lógica ni depender de floats.
    """

    PORCENTAJE_IMPUESTO = Decimal('0.19')
    VENCIMIENTO_DIAS = 15

    @staticmethod
    def _to_decimal(value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if value is None:
            return Decimal('0.00')
        return Decimal(str(value))

    @classmethod
    def calcular_totales(cls, subtotal: Any, porcentaje_impuesto: Any = None, descuento: Any = None) -> Dict[str, Decimal]:
        subtotal_decimal = cls._to_decimal(subtotal)
        impuesto_decimal = cls._to_decimal(porcentaje_impuesto if porcentaje_impuesto is not None else cls.PORCENTAJE_IMPUESTO)
        descuento_decimal = cls._to_decimal(descuento if descuento is not None else Decimal('0.00'))

        if impuesto_decimal > Decimal('1'):
            impuesto_decimal = impuesto_decimal / Decimal('100')

        # El impuesto debe calcularse sobre el importe neto después del descuento.
        # Este enfoque evita errores de punto flotante y mantiene la factura consistente.
        subtotal_neto = subtotal_decimal - descuento_decimal
        impuesto = subtotal_neto * impuesto_decimal
        total = subtotal_neto + impuesto

        return {
            'subtotal': subtotal_decimal.quantize(Decimal('0.01')),
            'impuesto': impuesto.quantize(Decimal('0.01')),
            'descuento': descuento_decimal.quantize(Decimal('0.01')),
            'total': total.quantize(Decimal('0.01')),
        }

    @classmethod
    def generar_numero_factura(cls, anio: Optional[int] = None, secuencia: Optional[int] = None) -> str:
        if anio is None:
            anio = datetime.now().year

        if secuencia is None:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) AS count FROM factura')
            result = cur.fetchone()
            cur.close()
            conn.close()
            secuencia = int(result['count'] if result else 0) + 1

        return f'FAC-{anio}-{secuencia:06d}'

    @classmethod
    def actualizar_estado(cls, id_factura: int, nuevo_estado: str, conn: Any = None, cur: Any = None) -> bool:
        """Actualiza el estado de una factura sin romper la transacción del caller."""
        owns_connection = conn is None
        if owns_connection:
            conn = get_connection()
            cur = conn.cursor()

        try:
            cur.execute('UPDATE factura SET estado_factura = %s WHERE id_factura = %s', (nuevo_estado, id_factura))
            if owns_connection:
                conn.commit()
            return True
        except Exception:
            if owns_connection:
                conn.rollback()
            raise
        finally:
            if owns_connection and cur is not None:
                cur.close()
            if owns_connection and conn is not None:
                conn.close()

    @classmethod
    def construir_pdf_factura(cls, factura: Dict[str, Any], items: List[Dict[str, Any]], base_url: str) -> bytes:

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        story = []

        # Título y Encabezado de Factura
        story.append(Paragraph(f"<b>OIL SKIN - FACTURA DE VENTA</b>", styles['Title']))
        story.append(Paragraph(f"Nº Factura: <b>{factura.get('numero_factura', 'FAC-000')}</b>", styles['Heading2']))
        story.append(Spacer(1, 0.15 * inch))

        # Información general del pedido y método de pago
        metodo = str(factura.get('metodo_pago', 'efectivo')).upper()
        estado = str(factura.get('estado_factura', 'emitida')).capitalize()
        fecha = str(factura.get('fecha_factura', ''))

        datos_factura = [
            [Paragraph("<b>Fecha de Emisión:</b>", styles['Normal']), Paragraph(fecha, styles['Normal']),
             Paragraph("<b>Método de Pago:</b>", styles['Normal']), Paragraph(f"<font color='#0284c7'><b>{metodo}</b></font>", styles['Normal'])],
            [Paragraph("<b>Estado del Pedido:</b>", styles['Normal']), Paragraph(estado, styles['Normal']),
             Paragraph("<b>Moneda:</b>", styles['Normal']), Paragraph("COP ($)", styles['Normal'])],
        ]
        t_info = Table(datos_factura, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        t_info.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_info)
        story.append(Spacer(1, 0.15 * inch))

        # Detalles del Cliente
        nombre = str(factura.get('cliente_nombre', 'Cliente General'))
        email = str(factura.get('cliente_email', 'N/A'))
        celular = str(factura.get('cliente_celular', 'N/A'))
        direccion = str(factura.get('direccion_entrega', 'N/A'))
        ciudad = str(factura.get('ciudad', ''))

        datos_cliente = [
            [Paragraph("<b>DATOS DEL CLIENTE Y ENVÍO</b>", styles['Heading3']), ""],
            [Paragraph("<b>Nombre Completo:</b>", styles['Normal']), Paragraph(nombre, styles['Normal'])],
            [Paragraph("<b>Correo Electrónico:</b>", styles['Normal']), Paragraph(email, styles['Normal'])],
            [Paragraph("<b>Teléfono Contacto:</b>", styles['Normal']), Paragraph(celular, styles['Normal'])],
            [Paragraph("<b>Dirección de Entrega:</b>", styles['Normal']), Paragraph(f"{direccion} ({ciudad})" if ciudad else direccion, styles['Normal'])],
        ]
        t_cliente = Table(datos_cliente, colWidths=[2*inch, 5*inch])
        t_cliente.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#e0f2fe')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor('#0369a1')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bae6fd')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_cliente)
        story.append(Spacer(1, 0.2 * inch))

        # Tabla de Productos
        story.append(Paragraph("<b>DETALLE DE PRODUCTOS</b>", styles['Heading3']))
        story.append(Spacer(1, 0.05 * inch))

        table_data = [['Producto', 'Cantidad', 'Precio Unitario', 'Subtotal']]
        for item in items:
            table_data.append([
                item.get('descripcion', 'Producto'),
                str(item.get('cantidad', 0)),
                f"${item.get('precio_unitario', 0):,.2f}",
                f"${item.get('total_linea', 0):,.2f}",
            ])
        table = Table(table_data, colWidths=[3.5*inch, 1*inch, 1.25*inch, 1.25*inch], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.15 * inch))

        # Totales
        subtotal_val = f"${factura.get('subtotal', 0):,.2f}"
        total_val = f"${factura.get('total', 0):,.2f}"

        datos_totales = [
            ["Subtotal:", subtotal_val],
            ["Descuento / Impuestos:", "$0.00 COP"],
            [Paragraph("<b>TOTAL PAGADO:</b>", styles['Normal']), Paragraph(f"<b><font color='#0369a1' size='12'>{total_val} COP</font></b>", styles['Normal'])],
        ]
        t_totales = Table(datos_totales, colWidths=[5*inch, 2*inch])
        t_totales.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#0284c7')),
        ]))
        story.append(t_totales)

        # Código QR de Verificación
        qr_url = f"{base_url}/factura/{factura.get('id_factura', 1)}"
        qr = qrcode.make(qr_url)
        qr_bytes = BytesIO()
        qr.save(qr_bytes, format='PNG')
        qr_bytes.seek(0)

        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph('Verifique la validez de esta factura escaneando el código QR:', styles['Italic']))
        story.append(Spacer(1, 0.05 * inch))
        story.append(Image(qr_bytes, width=1.5 * inch, height=1.5 * inch))

        doc.build(story)
        return buffer.getvalue()


    @classmethod
    def crear_desde_pedido(
        cls,
        id_pedido: int,
        id_usuario: int,
        metodo_pago: str,
        items: List[Dict[str, Any]],
        descuento: Any = None,
        estado_factura: str = 'emitida',
        conn: Any = None,
        cur: Any = None,
    ) -> Dict[str, Any]:
        """Crea una factura y sus líneas de detalle en una sola transacción."""
        owns_connection = conn is None
        if owns_connection:
            conn = get_connection()
            cur = conn.cursor()

        try:
            subtotal = sum(cls._to_decimal(item['precio_unitario']) * Decimal(item['cantidad']) for item in items)
            totales = cls.calcular_totales(subtotal=subtotal, descuento=descuento)
            numero_factura = cls.generar_numero_factura()
            fecha_factura = datetime.now()
            fecha_vencimiento = fecha_factura + timedelta(days=cls.VENCIMIENTO_DIAS)

            cur.execute(
                """
                INSERT INTO factura (
                    id_pedido, subtotal, total, metodo_pago
                ) VALUES (%s, %s, %s, %s)
                """,
                (
                    id_pedido,
                    totales['subtotal'],
                    totales['total'],
                    metodo_pago,
                ),
            )
            id_factura = cur.lastrowid

            for item in items:
                precio_unitario = cls._to_decimal(item['precio_unitario'])
                cantidad = int(item['cantidad'])
                subtotal_linea = precio_unitario * Decimal(cantidad)
                cur.execute(
                    """
                    INSERT INTO detalle_pedido (
                        id_pedido, id_producto, cantidad, precio_unitario, subtotal
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        id_pedido,
                        item['id_producto'],
                        cantidad,
                        precio_unitario,
                        subtotal_linea,
                    ),
                )

            if owns_connection:
                conn.commit()
            return {
                'id_factura': id_factura,
                'id_pedido': id_pedido,
                'id_usuario': id_usuario,
                'numero_factura': numero_factura,
                'fecha_factura': fecha_factura,
                'fecha_vencimiento': fecha_vencimiento,
                'estado_factura': estado_factura,
                'subtotal': totales['subtotal'],
                'impuesto': totales['impuesto'],
                'descuento': totales['descuento'],
                'total': totales['total'],
                'metodo_pago': metodo_pago,
            }
        except Exception:
            if owns_connection:
                conn.rollback()
            raise
        finally:
            if owns_connection and cur is not None:
                cur.close()
            if owns_connection and conn is not None:
                conn.close()
