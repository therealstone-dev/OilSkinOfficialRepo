from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app

def _get_serializer():
    secret_key = current_app.config.get('SECRET_KEY', 'dev-secret-key')
    return URLSafeTimedSerializer(secret_key)

def generate_reset_token(email: str, user_id: int = None, salt: str = 'oilskin-password-reset') -> str:
    """Genera un token seguro con expiración temporal para recuperación de contraseña."""
    serializer = _get_serializer()
    payload = {
        'email': email,
        'user_id': user_id
    }
    return serializer.dumps(payload, salt=salt)

def verify_reset_token(token: str, max_age: int = 3600, salt: str = 'oilskin-password-reset') -> dict | None:
    """Verifica y decodifica un token de recuperación. Retorna el payload si es válido, o None si expiró/inválido."""
    serializer = _get_serializer()
    try:
        payload = serializer.loads(token, salt=salt, max_age=max_age)
        return payload
    except (SignatureExpired, BadSignature, Exception):
        return None
