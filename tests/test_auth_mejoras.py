import pytest
import hashlib
from app import app
from src.services.oauth_service import is_google_oauth_configured, get_google_auth_url
from src.models.ModeloUsuario import ModeloUsuario
from src.database.db_mysql import get_connection

def test_google_oauth_service():
    # Verifica que la función de configuración y generación de URL opere correctamente
    auth_url = get_google_auth_url(redirect_uri="http://localhost:5000/auth/google/callback", state="test_state_123")
    assert "https://accounts.google.com/o/oauth2/v2/auth" in auth_url
    assert "client_id=" in auth_url
    assert "state=test_state_123" in auth_url
    assert "redirect_uri=" in auth_url
    assert "scope=openid+email+profile" in auth_url or "scope=openid%20email%20profile" in auth_url

def test_otp_code_lifecycle():
    with app.app_context():
        # Crear o buscar un usuario de pruebas
        test_email = "test_otp_user@oilskin.test"
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM usuario WHERE email = %s", (test_email,))
        conn.commit()

        # Insertar usuario base
        user_id = ModeloUsuario.create(
            nombre="Usuario Test OTP",
            email=test_email,
            password="password123",
            direccion="Calle Falsa 123",
            celular="3001234567"
        )
        assert user_id is not None

        # 1. Generar código OTP
        codigo_plano = "123456"
        codigo_hash = hashlib.sha256(codigo_plano.encode('utf-8')).hexdigest()

        # Guardar código
        ok = ModeloUsuario.guardar_codigo_recuperacion(user_id, codigo_hash, minutos_validez=15)
        assert ok is True

        # 2. Probar código erróneo
        ok_wrong, msg_wrong, _ = ModeloUsuario.verificar_codigo_recuperacion(test_email, "999999")
        assert ok_wrong is False
        assert "incorrecto" in msg_wrong.lower()

        # 3. Probar código correcto
        ok_correct, msg_correct, user_data = ModeloUsuario.verificar_codigo_recuperacion(test_email, "123456")
        assert ok_correct is True
        assert user_data is not None
        assert "correctamente" in msg_correct.lower()

        # 4. Verificar que el código ya no puede reutilizarse
        ok_reuse, msg_reuse, _ = ModeloUsuario.verificar_codigo_recuperacion(test_email, "123456")
        assert ok_reuse is False
        assert "no hay ningún código" in msg_reuse.lower() or "activo" in msg_reuse.lower()

        # Limpieza
        cur.execute("DELETE FROM usuario WHERE email = %s", (test_email,))
        conn.commit()
        cur.close()
        conn.close()

def test_google_user_creation_and_linking():
    with app.app_context():
        test_email = "test_google_user@oilskin.test"
        test_google_id = "google_sub_9876543210"

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM usuario WHERE email = %s OR google_id = %s", (test_email, test_google_id))
        conn.commit()

        # 1. Crear usuario vía Google
        new_id = ModeloUsuario.create_google_user(
            nombre="Google User Test",
            email=test_email,
            google_id=test_google_id,
            foto_perfil="https://lh3.googleusercontent.com/test_avatar.jpg"
        )
        assert new_id is not None

        # 2. Buscar por google_id
        user = ModeloUsuario.get_by_google_id(test_google_id)
        assert user is not None
        assert user['email'] == test_email
        assert user['auth_provider'] == 'google'
        assert user['foto_perfil'] == "https://lh3.googleusercontent.com/test_avatar.jpg"

        # 3. Probar linking
        second_email = "test_link_user@oilskin.test"
        cur.execute("DELETE FROM usuario WHERE email = %s", (second_email,))
        conn.commit()
        local_id = ModeloUsuario.create(
            nombre="Local User Test",
            email=second_email,
            password="localpassword",
            direccion="Carrera 10 # 20-30",
            celular="3109876543"
        )
        assert local_id is not None

        link_ok = ModeloUsuario.link_google_account(local_id, "google_sub_link_112233", "https://avatar.test/img.png")
        assert link_ok is True

        linked_user = ModeloUsuario.get_by_google_id("google_sub_link_112233")
        assert linked_user is not None
        assert linked_user['id_usuario'] == local_id
        assert linked_user['auth_provider'] == 'google'

        # Limpieza
        cur.execute("DELETE FROM usuario WHERE email IN (%s, %s)", (test_email, second_email))
        conn.commit()
        cur.close()
        conn.close()
