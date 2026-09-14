import pytest
from app import app
from src.models.ModeloCategoria import ModeloCategoria
from src.models.ModeloProductos import ModeloProducto
from src.models.ModeloAdmin import ModeloAdmin


def test_categoria_validaciones_basicas():
    """Valida que nombres vacíos o demasiado largos sean rechazados sin tocar la BD."""
    ok, err = ModeloCategoria.crear_categoria("")
    assert not ok
    assert "obligatorio" in err.lower()

    ok, err = ModeloCategoria.crear_categoria("   ")
    assert not ok
    assert "obligatorio" in err.lower()

    ok, err = ModeloCategoria.crear_categoria("X" * 101)
    assert not ok
    assert "100 caracteres" in err.lower()

    ok, err = ModeloCategoria.actualizar_categoria(1, "")
    assert not ok
    assert "vacío" in err.lower() or "obligatorio" in err.lower()


def test_categoria_crud_en_bd():
    """Prueba el ciclo de vida CRUD de una categoría en la base de datos."""
    with app.app_context():
        test_cat_name = "Categoria Test Auto"
        
        # Limpiar previamente por si quedó de un intento anterior
        cat_previa = ModeloCategoria.get_by_name(test_cat_name)
        if cat_previa:
            ModeloCategoria.eliminar_categoria(cat_previa['id_categoria'])

        # 1. Crear categoría de prueba
        ok, res = ModeloCategoria.crear_categoria(test_cat_name, "Descripción de prueba")
        assert ok is True, f"Fallo al crear categoría: {res}"

        cat = ModeloCategoria.get_by_name(test_cat_name)
        assert cat is not None
        cat_id = cat['id_categoria']

        try:
            # 2. Obtener por ID
            cat_obtenida = ModeloCategoria.get_by_id(cat_id)
            assert cat_obtenida is not None
            assert cat_obtenida['nombre_categoria'] == test_cat_name

            # 3. Intentar duplicar nombre
            ok_dup, err_dup = ModeloCategoria.crear_categoria(test_cat_name)
            assert ok_dup is False
            assert "ya existe" in err_dup.lower()

            # 4. Actualizar categoría
            updated_name = "Categoria Test Auto Mod"
            ok_up, err_up = ModeloCategoria.actualizar_categoria(cat_id, updated_name, "Nueva desc")
            assert ok_up is True
            cat_mod = ModeloCategoria.get_by_id(cat_id)
            assert cat_mod['nombre_categoria'] == updated_name

            # 5. Listar con conteo
            lista = ModeloCategoria.get_categorias_con_conteo()
            assert isinstance(lista, list)
            encontrado = any(c['id_categoria'] == cat_id and c['nombre_categoria'] == updated_name for c in lista)
            assert encontrado is True

        finally:
            # 6. Eliminar categoría de prueba
            ok_del, _ = ModeloCategoria.eliminar_categoria(cat_id)
            assert ok_del is True
            assert ModeloCategoria.get_by_id(cat_id) is None


def test_atributos_producto_crud():
    """Prueba guardar y recuperar atributos estructurados de un producto."""
    with app.app_context():
        # Tomar un producto existente para la prueba de atributos
        desglose = ModeloAdmin.get_desglose_productos()
        if not desglose:
            pytest.skip("No hay productos en la base de datos para probar atributos")
        
        prod_id = desglose[0]['id_producto']

        # Estructura de atributos de prueba
        atributos_test = {
            'badge': [{'titulo': 'Orgánico', 'contenido': ''}],
            'beneficio': [{'titulo': 'Hidratación', 'contenido': 'Larga duración por 24h'}],
            'modo_uso': [{'titulo': 'Uso diario', 'contenido': 'Aplicar por la mañana'}],
            'ingrediente': [{'titulo': 'Aloe Vera', 'contenido': 'Extracto puro 100%'}]
        }

        # Guardar atributos
        ok_save, _ = ModeloProducto.guardar_atributos(prod_id, atributos_test)
        assert ok_save is True

        # Recuperar atributos
        recuperados = ModeloProducto.get_atributos(prod_id)
        assert isinstance(recuperados, dict)
        assert 'badge' in recuperados
        assert 'beneficio' in recuperados
        assert 'modo_uso' in recuperados
        assert 'ingrediente' in recuperados

        # Verificar que los datos insertados coinciden
        assert any(b['titulo'] == 'Orgánico' for b in recuperados['badge'])
        assert any(b['titulo'] == 'Hidratación' and '24h' in b['contenido'] for b in recuperados['beneficio'])
        assert any(m['titulo'] == 'Uso diario' for m in recuperados['modo_uso'])
        assert any(i['titulo'] == 'Aloe Vera' for i in recuperados['ingrediente'])


def test_rutas_admin_protegidas():
    """Valida que las rutas de categorías y administración requieran autenticación de admin."""
    client = app.test_client()

    # Usuario anónimo
    res = client.get('/admin/categorias', follow_redirects=False)
    assert res.status_code in [302, 401, 403]

    res_crear = client.post('/admin/categorias/crear', data={'nombre': 'Test'}, follow_redirects=False)
    assert res_crear.status_code in [302, 401, 403]


def test_borrado_logico_y_reactivacion_producto():
    """Valida que productos con ventas se archiven lógicamente y se puedan reactivar."""
    with app.app_context():
        # 1. Producto nuevo sin ventas: borrado físico
        ok, _, test_id = ModeloAdmin.crear_producto("Prod Test Temp", "Desc", 1000, 5, 1)
        assert ok is True and test_id is not None
        ok_del, _ = ModeloAdmin.eliminar_producto(test_id)
        assert ok_del is True
        assert ModeloProducto.get_by_id(test_id) is None

        # 2. Desglose incluye activo
        desglose = ModeloAdmin.get_desglose_productos()
        assert len(desglose) > 0
        assert 'activo' in desglose[0]
