import pytest
from src.services.geolocalizacion_service import (
    normalizar_direccion,
    resolver_malla_bogota,
    validar_coordenadas,
    geocodificar_direccion,
    geocodificar_inverso,
    buscar_sugerencias,
    DEFAULT_LAT,
    DEFAULT_LNG,
    _GEOCODE_CACHE
)


def test_normalizar_direccion():
    assert normalizar_direccion("cll 100 # 15-20") == "Calle 100 # 15-20"
    assert normalizar_direccion("cra 7 no 72 - 10") == "Carrera 7 # 72 - 10"
    assert normalizar_direccion("diag 45a sur # 12 este") == "Diagonal 45A Sur # 12 Este"
    assert normalizar_direccion("  avda chile nro 10-20  ") == "Avenida Chile # 10-20"
    assert normalizar_direccion("") == ""
    assert normalizar_direccion(None) == ""


def test_resolver_malla_bogota():
    res = resolver_malla_bogota("Calle 72 # 10-20")
    assert res is not None
    assert "lat" in res and "lng" in res
    # Calle 72 en Bogotá debe estar alrededor de lat 4.65 - 4.67
    assert 4.60 <= res['lat'] <= 4.70
    # Carrera 10 debe estar alrededor de lng -74.05 a -74.12
    assert -74.15 <= res['lng'] <= -74.05
    assert res['precision'] == 'exacto'


def test_validar_coordenadas():
    # Coordenadas válidas en Bogotá
    assert validar_coordenadas(4.6533, -74.0836, 'Bogotá') is True
    assert validar_coordenadas(4.57409, -74.08958, 'Bogotá') is True

    # Coordenadas fuera de Bogotá pero válidas en Colombia
    assert validar_coordenadas(6.2442, -75.5812, 'Medellín') is True
    assert validar_coordenadas(6.2442, -75.5812, 'Bogotá') is False

    # Coordenadas inválidas / fuera del país / nulas
    assert validar_coordenadas(None, -74.0) is False
    assert validar_coordenadas(50.0, 10.0) is False  # Europa
    assert validar_coordenadas("invalido", -74.0) is False


def test_geocodificar_direccion_valida():
    resultado = geocodificar_direccion("Calle 100 # 15-20", ciudad="Bogotá")
    assert isinstance(resultado, dict)
    assert "lat" in resultado and "lng" in resultado
    assert "direccion_normalizada" in resultado
    assert "precision" in resultado
    assert validar_coordenadas(resultado['lat'], resultado['lng'], 'Bogotá') is True
    assert resultado['error'] is None


def test_geocodificar_direccion_vacia():
    resultado = geocodificar_direccion("", ciudad="Bogotá")
    assert resultado['lat'] == DEFAULT_LAT
    assert resultado['lng'] == DEFAULT_LNG
    assert resultado['precision'] == 'desconocido'
    assert resultado['error'] is not None


def test_caching_geocodificacion():
    _GEOCODE_CACHE.clear()
    res1 = geocodificar_direccion("Carrera 7 # 72-10", ciudad="Bogotá")
    res2 = geocodificar_direccion("Carrera 7 # 72-10", ciudad="Bogotá")
    assert res1 == res2
    # Debe estar en caché
    cache_key = "carrera 7 # 72-10|bogotá"
    assert cache_key in _GEOCODE_CACHE


def test_geocodificar_inverso():
    # Coordenadas del Parque Santander / Bogotá
    resultado = geocodificar_inverso(4.6015, -74.0725)
    assert isinstance(resultado, dict)
    assert "direccion" in resultado
    assert "ciudad" in resultado
    assert resultado['direccion'] != ""


def test_buscar_sugerencias():
    sugerencias = buscar_sugerencias("Calle 26", ciudad="Bogotá", limit=3)
    assert isinstance(sugerencias, list)
    if sugerencias:
        first = sugerencias[0]
        assert "direccion" in first
        assert "lat" in first and "lng" in first
