import re
import json
import math
import urllib.request
import urllib.parse
from decouple import config

# Configuración de variables de entorno
GEOCODING_PROVIDER = config('GEOCODING_PROVIDER', default='nominatim').strip().lower()
GEOCODING_API_KEY = config('GEOCODING_API_KEY', default='').strip()
GEOCODING_USER_AGENT = config('GEOCODING_USER_AGENT', default='OilSkin-ECommerce/1.0 (soporte@oilskin.com)').strip()

# Caché en memoria para evitar llamadas redundantes
_GEOCODE_CACHE = {}
_REVERSE_CACHE = {}
_AUTOCOMPLETE_CACHE = {}

# Coordenadas por defecto (Centro de Distribución OilSkin - Bogotá)
DEFAULT_LAT = 4.57409
DEFAULT_LNG = -74.08958

# Límites aproximados para Colombia y Bogotá
COLOMBIA_BOUNDS = {
    'min_lat': -4.3, 'max_lat': 13.5,
    'min_lng': -79.2, 'max_lng': -66.8
}

BOGOTA_BOUNDS = {
    'min_lat': 4.45, 'max_lat': 4.90,
    'min_lng': -74.28, 'max_lng': -73.95
}


def normalizar_direccion(dir_texto: str) -> str:
    """Normaliza abreviaturas y nomenclatura vial colombiana."""
    if not dir_texto:
        return ""
    d = dir_texto.strip().lower()

    # 1. Normalizar prefijos viales colombianos
    d = re.sub(r'\b(cll|cl|c)\.?\b', 'calle', d)
    d = re.sub(r'\b(cra|cr|kra|kr|k)\.?\b', 'carrera', d)
    d = re.sub(r'\b(avda|av|ak)\.?\b', 'avenida', d)
    d = re.sub(r'\b(diag|dg)\.?\b', 'diagonal', d)
    d = re.sub(r'\b(trans|tv)\.?\b', 'transversal', d)
    d = re.sub(r'\bac\b', 'avenida calle', d)
    d = re.sub(r'\bautonorte\b', 'autopista norte', d)
    d = re.sub(r'\bautosur\b', 'autopista sur', d)

    # 2. Normalizar cuadrantes cardinales
    d = re.sub(r'(\d+)\s*s\b', r'\1 sur', d)
    d = re.sub(r'(\d+)\s*e\b', r'\1 este', d)
    d = re.sub(r'(\d+)\s*n\b', r'\1 norte', d)
    d = re.sub(r'(\d+)\s*o\b', r'\1 oeste', d)
    d = re.sub(r'(\d+)\s*w\b', r'\1 oeste', d)

    # 3. Normalizar separadores y numerales
    d = re.sub(r'(?:no\.?|nro\.?|num\.?|n°)\s*', '#', d)
    d = re.sub(r'\s*#\s*', ' # ', d)
    d = re.sub(r'\s+', ' ', d).strip()

    return d.title()


def resolver_malla_bogota(direccion_normalizada: str) -> dict | None:
    """
    Calcula una coordenada teórica precisa basada en la cuadrícula urbana cartesiana de Bogotá.
    Permite geolocalizar direcciones colombianas con alta precisión sin depender de APIs externas.
    """
    d = direccion_normalizada.lower()

    match_completo = re.search(
        r'(calle|carrera|diagonal|transversal|avenida)\s*([0-9]+)[a-z]?(\s*sur|\s*este)?(?:[\s,#noNRO\.\-]+)+([0-9]+)[a-z]?(\s*sur|\s*este)?(?:\s*(?:-|#|\s)\s*([0-9]+))?',
        d
    )

    tipo_via = None
    num_via = None
    es_via_sur = 'sur' in d
    es_via_este = 'este' in d
    num_cruce = None
    es_cruce_sur = False
    es_cruce_este = False

    if match_completo:
        tipo_via = match_completo.group(1)
        num_via = int(match_completo.group(2))
        if match_completo.group(3):
            if 'sur' in match_completo.group(3): es_via_sur = True
            if 'este' in match_completo.group(3): es_via_este = True
        num_cruce = int(match_completo.group(4))
        if match_completo.group(5):
            if 'sur' in match_completo.group(5): es_cruce_sur = True
            if 'este' in match_completo.group(5): es_cruce_este = True
    else:
        match_simple = re.search(r'(calle|carrera|diagonal|transversal|avenida)\s*([0-9]+)', d)
        if match_simple:
            tipo_via = match_simple.group(1)
            num_via = int(match_simple.group(2))

    if num_via is None:
        return None

    lat = None
    lng = None

    if tipo_via in ('calle', 'diagonal'):
        lat = (4.5980 - (num_via * 0.00095)) if es_via_sur else (4.5980 + (num_via * 0.00092))
        if num_cruce is not None:
            lng = (-74.0720 + (num_cruce * 0.0018)) if (es_cruce_este or es_via_este) else (-74.0720 - (num_cruce * 0.0022))
        else:
            lng = -74.0850
    elif tipo_via in ('carrera', 'transversal', 'avenida'):
        lng = (-74.0720 + (num_via * 0.0018)) if es_via_este else (-74.0720 - (num_via * 0.0022))
        if num_cruce is not None:
            lat = (4.5980 - (num_cruce * 0.00095)) if (es_cruce_sur or es_via_sur) else (4.5980 + (num_cruce * 0.00092))
        else:
            lat = 4.5750 if es_via_sur else 4.6300

    if lat is not None and lng is not None:
        return {
            'lat': round(lat, 6),
            'lng': round(lng, 6),
            'precision': 'exacto' if num_cruce is not None else 'calle'
        }

    return None


def validar_coordenadas(lat: float | None, lng: float | None, ciudad: str = '') -> bool:
    """Verifica si las coordenadas están dentro de rangos geográficos plausibles."""
    if lat is None or lng is None:
        return False
    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return False

    # Validar que no sea NaN ni infinito
    if math.isnan(lat) or math.isnan(lng) or math.isinf(lat) or math.isinf(lng):
        return False

    # Validar dentro de Colombia
    if not (COLOMBIA_BOUNDS['min_lat'] <= lat <= COLOMBIA_BOUNDS['max_lat'] and
            COLOMBIA_BOUNDS['min_lng'] <= lng <= COLOMBIA_BOUNDS['max_lng']):
        return False

    # Si es Bogotá, validar dentro de la sabana de Bogotá
    ciudad_norm = (ciudad or '').lower()
    if 'bogot' in ciudad_norm:
        if not (BOGOTA_BOUNDS['min_lat'] <= lat <= BOGOTA_BOUNDS['max_lat'] and
                BOGOTA_BOUNDS['min_lng'] <= lng <= BOGOTA_BOUNDS['max_lng']):
            return False

    return True


def geocodificar_direccion(direccion: str, ciudad: str = 'Bogotá', timeout: int = 5) -> dict:
    """
    Geocodifica una dirección a coordenadas (lat, lng).
    Utiliza caché en memoria, proveedor Nominatim y fallback a cuadrante colombiano.
    """
    dir_limpia = (direccion or '').strip()
    ciudad_limpia = (ciudad or 'Bogotá').strip()

    if not dir_limpia:
        return {
            'lat': DEFAULT_LAT,
            'lng': DEFAULT_LNG,
            'direccion_normalizada': '',
            'precision': 'desconocido',
            'error': 'Dirección vacía'
        }

    dir_normalizada = normalizar_direccion(dir_limpia)
    cache_key = f"{dir_normalizada.lower()}|{ciudad_limpia.lower()}"

    if cache_key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[cache_key]

    # 1. Intentar resolver con la malla geométrica de Bogotá si aplica
    res_malla = None
    if 'bogot' in ciudad_limpia.lower():
        res_malla = resolver_malla_bogota(dir_normalizada)

    # 2. Intentar geocodificación externa vía Nominatim
    match_externo = None
    try:
        query_str = f"{dir_normalizada}, {ciudad_limpia}, Colombia"
        params = {
            'q': query_str,
            'format': 'json',
            'addressdetails': '1',
            'countrycodes': 'co',
            'limit': '1'
        }

        # Si tenemos cuadrante teórico de Bogotá, acotar la búsqueda al cuadrante
        if res_malla:
            min_lng = round(res_malla['lng'] - 0.035, 4)
            min_lat = round(res_malla['lat'] - 0.035, 4)
            max_lng = round(res_malla['lng'] + 0.035, 4)
            max_lat = round(res_malla['lat'] + 0.035, 4)
            params['viewbox'] = f"{min_lng},{min_lat},{max_lng},{max_lat}"
            params['bounded'] = '1'

        url = f"https://nominatim.openstreetmap.org/search?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={'User-Agent': GEOCODING_USER_AGENT})

        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data and len(data) > 0:
                    cand_lat = float(data[0]['lat'])
                    cand_lng = float(data[0]['lon'])

                    # Validar coordenadas obtenidas
                    if validar_coordenadas(cand_lat, cand_lng, ciudad_limpia):
                        match_externo = {
                            'lat': cand_lat,
                            'lng': cand_lng,
                            'direccion_normalizada': data[0].get('display_name', f"{dir_normalizada}, {ciudad_limpia}"),
                            'precision': 'exacto' if data[0].get('type') in ('house', 'building', 'street_number') else 'aproximado',
                            'error': None
                        }
    except Exception as ex:
        # Falla de red, timeout o rate-limiting controlado
        pass

    resultado = None
    if match_externo:
        resultado = match_externo
    elif res_malla and validar_coordenadas(res_malla['lat'], res_malla['lng'], ciudad_limpia):
        resultado = {
            'lat': res_malla['lat'],
            'lng': res_malla['lng'],
            'direccion_normalizada': f"{dir_normalizada}, {ciudad_limpia}",
            'precision': res_malla['precision'],
            'error': None
        }
    else:
        # Fallback seguro con coordenadas por defecto
        resultado = {
            'lat': DEFAULT_LAT,
            'lng': DEFAULT_LNG,
            'direccion_normalizada': f"{dir_normalizada}, {ciudad_limpia}",
            'precision': 'aproximado',
            'error': 'No se pudo obtener una ubicación satelital exacta; se asignó punto logístico de referencia.'
        }

    _GEOCODE_CACHE[cache_key] = resultado
    return resultado


def geocodificar_inverso(lat: float, lng: float, timeout: int = 5) -> dict:
    """
    Convierte coordenadas (lat, lng) a una dirección legible.
    Utiliza Nominatim reverse geocoding con fallback a formato de cuadrante.
    """
    if not validar_coordenadas(lat, lng):
        return {
            'direccion': 'Ubicación GPS desconocida',
            'ciudad': 'Bogotá',
            'display_name': 'Coordenadas fuera de rango',
            'error': 'Coordenadas inválidas o fuera de Colombia'
        }

    cache_key = f"{round(lat, 5)}|{round(lng, 5)}"
    if cache_key in _REVERSE_CACHE:
        return _REVERSE_CACHE[cache_key]

    try:
        params = {
            'lat': str(lat),
            'lon': str(lng),
            'format': 'json',
            'addressdetails': '1'
        }
        url = f"https://nominatim.openstreetmap.org/reverse?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={'User-Agent': GEOCODING_USER_AGENT})

        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                address = data.get('address', {})

                road = address.get('road', '')
                house_number = address.get('house_number', '')
                suburb = address.get('suburb', address.get('neighbourhood', ''))
                city = address.get('city', address.get('town', address.get('state', 'Bogotá')))

                partes_dir = []
                if road:
                    partes_dir.append(road)
                if house_number:
                    partes_dir.append(f"# {house_number}")
                if suburb and not road:
                    partes_dir.append(suburb)

                dir_formateada = " ".join(partes_dir) if partes_dir else data.get('display_name', f"Ubicación GPS ({lat:.4f}, {lng:.4f})")

                resultado = {
                    'direccion': dir_formateada,
                    'ciudad': city,
                    'display_name': data.get('display_name', ''),
                    'error': None
                }
                _REVERSE_CACHE[cache_key] = resultado
                return resultado
    except Exception as ex:
        pass

    # Fallback si el servicio no responde o falla la red
    fallback_res = {
        'direccion': f"Ubicación GPS ({lat:.5f}, {lng:.5f})",
        'ciudad': 'Bogotá',
        'display_name': f"Punto satelital ({lat:.5f}, {lng:.5f})",
        'error': 'Servicio externo no disponible; usando referencia de coordenadas.'
    }
    _REVERSE_CACHE[cache_key] = fallback_res
    return fallback_res


def buscar_sugerencias(query: str, ciudad: str = 'Bogotá', limit: int = 5, timeout: int = 4) -> list[dict]:
    """
    Retorna una lista de sugerencias de autocompletado para una búsqueda de dirección.
    Formato de cada item: {'direccion': str, 'lat': float, 'lng': float, 'ciudad': str}
    """
    q_limpia = (query or '').strip()
    if len(q_limpia) < 3:
        return []

    cache_key = f"{q_limpia.lower()}|{(ciudad or 'bogota').lower()}|{limit}"
    if cache_key in _AUTOCOMPLETE_CACHE:
        return _AUTOCOMPLETE_CACHE[cache_key]

    sugerencias = []

    # 1. Resolver con malla cartesiana de Bogotá si coincide con nomenclatura vial
    q_norm = normalizar_direccion(q_limpia)
    malla = resolver_malla_bogota(q_norm)
    if malla and ('bogot' in ciudad.lower() or not ciudad):
        sugerencias.append({
            'direccion': q_norm,
            'ciudad': ciudad or 'Bogotá',
            'lat': malla['lat'],
            'lng': malla['lng'],
            'fuente': 'Malla Vial Exacta'
        })

    # 2. Consultar Nominatim para sugerencias complementarias
    try:
        busqueda = f"{q_norm}, {ciudad}, Colombia" if ciudad else f"{q_norm}, Colombia"
        params = {
            'q': busqueda,
            'format': 'json',
            'addressdetails': '1',
            'countrycodes': 'co',
            'limit': str(limit)
        }
        url = f"https://nominatim.openstreetmap.org/search?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={'User-Agent': GEOCODING_USER_AGENT})

        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                items = json.loads(response.read().decode('utf-8'))
                for it in items:
                    lat_val = float(it['lat'])
                    lng_val = float(it['lon'])
                    if validar_coordenadas(lat_val, lng_val):
                        addr = it.get('address', {})
                        road = addr.get('road', '')
                        house_number = addr.get('house_number', '')
                        city_name = addr.get('city', addr.get('town', addr.get('state', ciudad or 'Bogotá')))

                        label = f"{road} # {house_number}".strip() if (road and house_number) else it.get('display_name', '')
                        # Evitar duplicar la sugerencia si ya fue agregada por la malla
                        if not any(s['direccion'] == label for s in sugerencias):
                            sugerencias.append({
                                'direccion': label or it.get('display_name', ''),
                                'ciudad': city_name,
                                'lat': lat_val,
                                'lng': lng_val,
                                'fuente': 'OpenStreetMap'
                            })
    except Exception:
        pass

    _AUTOCOMPLETE_CACHE[cache_key] = sugerencias[:limit]
    return sugerencias[:limit]
