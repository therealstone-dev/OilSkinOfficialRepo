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

    # Información corporativa y tributaria legal (OilSkin S.A.S.)
    EMISOR_NOMBRE = "OILSKIN S.A.S."
    EMISOR_NIT = "901.654.321-8"
    EMISOR_REGIMEN = "Responsable de IVA - Régimen Común"
    EMISOR_DIRECCION = "Calle 100 # 15-20, Oficina 502"
    EMISOR_CIUDAD = "Bogotá D.C., Colombia"
    EMISOR_TELEFONO = "+57 (601) 555-0199 / 300 123 4567"
    EMISOR_EMAIL = "facturacion@oilskin.com.co"
    RESOLUCION_DIAN = "Resolución DIAN No. 18760001234567 de 2026-01-15 | Habilitación de Facturación Electrónica FAC-2026-000001 a FAC-2026-999999"
    LEYENDA_LEGAL = "Esta factura de venta es un título valor según el Art. 774 del Código de Comercio. Productos cosméticos con registro sanitario INVIMA."

    @staticmethod
    def _to_decimal(value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if value is None:
            return Decimal('0.00')
        return Decimal(str(value))

    @staticmethod
    def numero_a_letras(numero: Any) -> str:
        """Convierte una cifra decimal a su equivalente en texto en pesos colombianos (M/CTE)."""
        units = ("", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE", "DIEZ", 
                 "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE")
        tens = ("", "", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA")
        hundreds = ("", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS", 
                    "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS")

        def _convert_group(n: int) -> str:
            if n == 0:
                return ""
            if n == 100:
                return "CIEN"
            res = []
            c = n // 100
            d = (n % 100) // 10
            u = n % 10
            if c > 0:
                res.append(hundreds[c])
            if n % 100 < 20:
                if n % 100 > 0:
                    res.append(units[n % 100])
            else:
                if d == 2 and u > 0:
                    res.append(f"VEINTI{units[u]}")
                else:
                    if d > 0:
                        res.append(tens[d])
                    if u > 0:
                        res.append(f"Y {units[u]}")
            return " ".join(res)

        val = FacturacionService._to_decimal(numero).quantize(Decimal('0.01'))
        ent = int(val)
        cent = int((val - Decimal(ent)) * 100)

        if ent == 0:
            str_ent = "CERO"
        else:
            millions = ent // 1_000_000
            thousands = (ent % 1_000_000) // 1_000
            rem = ent % 1_000

            parts = []
            if millions == 1:
                parts.append("UN MILLÓN")
            elif millions > 1:
                parts.append(f"{_convert_group(millions)} MILLONES")

            if thousands == 1:
                parts.append("MIL")
            elif thousands > 1:
                parts.append(f"{_convert_group(thousands)} MIL")

            if rem > 0:
                parts.append(_convert_group(rem))

            str_ent = " ".join(parts)

        return f"SON: {str_ent} PESOS {cent:02d}/100 M/CTE."

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

        # Header Corporativo Emisor
        story.append(Paragraph(f"<b><font size=16 color='#0f172a'>{cls.EMISOR_NOMBRE}</font></b>", styles['Normal']))
        story.append(Paragraph(f"<font size=9 color='#475569'><b>NIT:</b> {cls.EMISOR_NIT} | {cls.EMISOR_REGIMEN}</font>", styles['Normal']))
        story.append(Paragraph(f"<font size=9 color='#475569'><b>Dirección:</b> {cls.EMISOR_DIRECCION} - {cls.EMISOR_CIUDAD}</font>", styles['Normal']))
        story.append(Paragraph(f"<font size=9 color='#475569'><b>Contacto:</b> {cls.EMISOR_TELEFONO} | {cls.EMISOR_EMAIL}</font>", styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))

        # Cuadro de Número de Factura y Resolución
        num_fac = factura.get('numero_factura', 'FAC-000')
        fecha_fac = str(factura.get('fecha_factura', ''))
        fecha_venc = str(factura.get('fecha_vencimiento', ''))
        metodo = str(factura.get('metodo_pago', 'efectivo')).upper()
        estado = str(factura.get('estado_factura', 'emitida')).upper()

        datos_encabezado = [
            [
                Paragraph(f"<b>FACTURA ELECTRÓNICA DE VENTA</b><br/><font size=12 color='#0284c7'><b>Nº {num_fac}</b></font>", styles['Normal']),
                Paragraph(f"<b>Fecha de Emisión:</b> {fecha_fac}<br/><b>Fecha Vencimiento:</b> {fecha_venc}<br/><b>Forma de Pago:</b> Contado ({metodo})<br/><b>Estado:</b> {estado}", styles['Normal'])
            ]
        ]
        t_enc = Table(datos_encabezado, colWidths=[3.5*inch, 3.5*inch])
        t_enc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#0284c7')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_enc)
        story.append(Spacer(1, 0.05 * inch))

        # Resolución DIAN
        story.append(Paragraph(f"<font size=7 color='#64748b'><b>AUTORIZACIÓN DIAN:</b> {cls.RESOLUCION_DIAN}</font>", styles['Normal']))
        story.append(Spacer(1, 0.15 * inch))

        # Detalles del Cliente (Adquirente)
        nombre = str(factura.get('cliente_nombre', 'Cliente General'))
        email = str(factura.get('cliente_email', 'N/A'))
        celular = str(factura.get('cliente_celular', 'N/A'))
        direccion = str(factura.get('direccion_entrega', 'N/A'))
        ciudad = str(factura.get('ciudad', 'Bogotá'))

        datos_cliente = [
            [Paragraph("<b>DATOS DEL ADQUIRENTE (CLIENTE)</b>", styles['Normal']), ""],
            [Paragraph("<b>Nombre / Razón Social:</b>", styles['Normal']), Paragraph(nombre, styles['Normal'])],
            [Paragraph("<b>Correo Electrónico:</b>", styles['Normal']), Paragraph(email, styles['Normal'])],
            [Paragraph("<b>Teléfono / Celular:</b>", styles['Normal']), Paragraph(celular, styles['Normal'])],
            [Paragraph("<b>Dirección de Envío:</b>", styles['Normal']), Paragraph(f"{direccion} - {ciudad}", styles['Normal'])],
        ]
        t_cliente = Table(datos_cliente, colWidths=[2*inch, 5*inch])
        t_cliente.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_cliente)
        story.append(Spacer(1, 0.15 * inch))

        # Tabla de Productos
        story.append(Paragraph("<b>DETALLE DE PRODUCTOS Y SERVICIOS</b>", styles['Normal']))
        story.append(Spacer(1, 0.05 * inch))

        table_data = [['Ítem / Descripción', 'Cant.', 'Precio Unitario', 'IVA %', 'Total Línea']]
        for item in items:
            p_unit = cls._to_decimal(item.get('precio_unitario', 0))
            cant = int(item.get('cantidad', 0))
            tot_linea = p_unit * Decimal(cant)
            table_data.append([
                Paragraph(str(item.get('descripcion', 'Producto')), styles['Normal']),
                str(cant),
                f"${p_unit:,.2f}",
                "19%",
                f"${tot_linea:,.2f}",
            ])

        table = Table(table_data, colWidths=[3.25*inch, 0.75*inch, 1.25*inch, 0.75*inch, 1.0*inch], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.15 * inch))

        # Resumen de Totales y Base Gravable
        subtotal_val = cls._to_decimal(factura.get('subtotal', 0))
        impuesto_val = cls._to_decimal(factura.get('impuesto', 0))
        descuento_val = cls._to_decimal(factura.get('descuento', 0))
        total_val = cls._to_decimal(factura.get('total', 0))

        if impuesto_val == Decimal('0.00') and subtotal_val > Decimal('0.00'):
            subtotal_neto = subtotal_val - descuento_val
            impuesto_val = (subtotal_neto * Decimal('0.19')).quantize(Decimal('0.01'))
            total_val = subtotal_neto + impuesto_val

        texto_letras = cls.numero_a_letras(total_val)

        datos_totales = [
            ["Subtotal (Base Gravable):", f"${subtotal_val:,.2f} COP"],
            ["Descuento Aplicado:", f"-${descuento_val:,.2f} COP"],
            ["IVA (19% Discriminado):", f"${impuesto_val:,.2f} COP"],
            [Paragraph("<b>TOTAL A PAGAR:</b>", styles['Normal']), Paragraph(f"<b><font color='#0369a1' size='11'>${total_val:,.2f} COP</font></b>", styles['Normal'])],
        ]
        t_totales = Table(datos_totales, colWidths=[5*inch, 2*inch])
        t_totales.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#0284c7')),
        ]))
        story.append(t_totales)
        story.append(Spacer(1, 0.1 * inch))

        # Total en letras
        story.append(Paragraph(f"<font size=8 color='#1e293b'><b>VALOR EN LETRAS:</b> {texto_letras}</font>", styles['Normal']))
        story.append(Spacer(1, 0.15 * inch))

        # QR y Verificación Digital
        qr_url = f"{base_url}/factura/{factura.get('id_factura', 1)}"
        qr = qrcode.make(qr_url)
        qr_bytes = BytesIO()
        qr.save(qr_bytes, format='PNG')
        qr_bytes.seek(0)

        cufe_simulado = f"CUFE-{factura.get('id_factura', 1):06d}-OILSKIN-2026"

        datos_qr = [
            [
                Image(qr_bytes, width=1.1 * inch, height=1.1 * inch),
                Paragraph(f"<font size=8 color='#475569'><b>VERIFICACIÓN DIGITAL Y SEGURIDAD</b><br/>Escanee este código QR o ingrese al portal web para consultar la autenticidad de este documento.<br/><b>Código Único (CUFE):</b> {cufe_simulado}<br/><b>Enlace:</b> {qr_url}</font>", styles['Normal'])
            ]
        ]
        t_qr = Table(datos_qr, colWidths=[1.3*inch, 5.7*inch])
        t_qr.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_qr)
        story.append(Spacer(1, 0.15 * inch))

        # Pie de página legal
        story.append(Paragraph(f"<para align='center'><font size=7 color='#64748b'><i>{cls.LEYENDA_LEGAL}</i></font></para>", styles['Normal']))

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
