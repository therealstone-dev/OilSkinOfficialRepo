from app import create_app

app = create_app()
client = app.test_client()

with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['cart'] = [
        {'id_producto': 1, 'nombre_producto': 'Test', 'precio_unitario': 10.0, 'cantidad': 1, 'subtotal': 10.0}
    ]

resp = client.post('/checkout', data={
    'metodo_pago': 'efectivo',
    'direccion_entrega': 'x',
    'ciudad': 'y',
    'telefono_contacto': 'z'
})
print(resp.status_code)
print(resp.headers.get('Location'))
print(resp.data[:200])
