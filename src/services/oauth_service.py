"""
Servicio de autenticación e integración OAuth 2.0 con Google para OilSkin.
Maneja la generación de URL de consentimiento, intercambio de tokens y obtención de perfil de usuario.
Implementado con la librería estándar de Python para máxima portabilidad, ligereza y cero dependencias frágiles.
"""
import json
import urllib.parse
import urllib.request
import urllib.error
from decouple import config

GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='').strip()
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='').strip()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def is_google_oauth_configured() -> bool:
    """Verifica si las credenciales de Google OAuth están configuradas en el entorno."""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and not GOOGLE_CLIENT_ID.startswith('tu_id'))


def get_google_auth_url(redirect_uri: str, state: str) -> str:
    """Construye la URL segura de autorización para redirigir al usuario a Google."""
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'online',
        'state': state,
        'prompt': 'select_account'
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_user_info(code: str, redirect_uri: str) -> tuple[bool, dict | str]:
    """
    Intercambia el código de autorización por tokens de acceso y obtiene el perfil de usuario.
    Retorna (True, user_info: dict) o (False, error_message: str).
    """
    if not is_google_oauth_configured():
        return False, "Google OAuth no está configurado en las variables de entorno (.env)."

    try:
        # 1. Intercambio de código por access_token
        token_data = urllib.parse.urlencode({
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }).encode('utf-8')

        token_req = urllib.request.Request(
            GOOGLE_TOKEN_URL,
            data=token_data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'OilSkin-ECommerce/1.0'
            },
            method='POST'
        )

        with urllib.request.urlopen(token_req, timeout=10) as token_response:
            token_json = json.loads(token_response.read().decode('utf-8'))

        access_token = token_json.get('access_token')
        if not access_token:
            return False, "No se recibió un access_token válido de Google."

        # 2. Consulta de información del usuario en Google UserInfo API
        userinfo_req = urllib.request.Request(
            GOOGLE_USERINFO_URL,
            headers={
                'Authorization': f'Bearer {access_token}',
                'User-Agent': 'OilSkin-ECommerce/1.0'
            },
            method='GET'
        )

        with urllib.request.urlopen(userinfo_req, timeout=10) as userinfo_response:
            user_info = json.loads(userinfo_response.read().decode('utf-8'))

        sub = user_info.get('sub')
        email = user_info.get('email', '').strip().lower()
        name = user_info.get('name', 'Usuario Google').strip()
        picture = user_info.get('picture')

        if not sub or not email:
            return False, "La respuesta de Google no incluyó el identificador o correo del usuario."

        return True, {
            'google_id': sub,
            'email': email,
            'name': name,
            'picture': picture,
            'email_verified': user_info.get('email_verified', False)
        }

    except urllib.error.HTTPError as http_err:
        try:
            err_body = http_err.read().decode('utf-8')
            err_json = json.loads(err_body)
            err_desc = err_json.get('error_description') or err_json.get('error') or err_body
        except Exception:
            err_desc = str(http_err)
        print(f"Error HTTP OAuth Google: {err_desc}")
        return False, f"Error en la autenticación de Google: {err_desc}"
    except Exception as ex:
        print(f"Error general OAuth Google: {ex}")
        return False, f"Error inesperado al conectar con Google: {ex}"
