import smtplib
import os
import json
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config


def _send_via_resend(to_email: str, subject: str, text_content: str, html_content: str, api_key: str, sender: str) -> tuple[bool, str]:
    """
    Envía correo a través de la API REST HTTPS de Resend (Puerto 443).
    No requiere puertos SMTP y funciona en Render, AWS, Vercel, etc.
    """
    try:
        url = "https://api.resend.com/emails"
        
        # Formatear remitente válido
        formatted_sender = sender
        if "@" not in formatted_sender:
            formatted_sender = "OilSkin <onboarding@resend.dev>"
        elif "<" not in formatted_sender:
            formatted_sender = f"OilSkin <{formatted_sender}>"

        payload = {
            "from": formatted_sender,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
            "text": text_content
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json",
                "User-Agent": "OilSkin-App/1.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status in (200, 201):
                return True, f"Correo enviado exitosamente a {to_email}"
            else:
                return False, f"Resend API respondió con código {resp.status}"
    except urllib.error.HTTPError as he:
        try:
            err_body = he.read().decode('utf-8')
            err_json = json.loads(err_body)
            msg = err_json.get('message', err_body)
        except Exception:
            msg = str(he)
        return False, f"Error en Resend API ({he.code}): {msg}"
    except Exception as ex:
        return False, f"Error de conexión con Resend: {str(ex)}"


def _send_via_smtp(to_email: str, subject: str, text_content: str, html_content: str) -> tuple[bool, str]:
    """
    Envía correo a través de conexión SMTP tradicional (para desarrollo local).
    """
    mail_server = config('MAIL_SERVER', default='smtp.gmail.com')
    mail_port = config('MAIL_PORT', default=587, cast=int)
    mail_username = config('MAIL_USERNAME', default='')
    mail_password = config('MAIL_PASSWORD', default='')
    mail_sender = config('MAIL_DEFAULT_SENDER', default=mail_username if mail_username else 'no-reply@oilskin.com')
    mail_use_tls = config('MAIL_USE_TLS', default=True, cast=bool)
    mail_use_ssl = config('MAIL_USE_SSL', default=False, cast=bool)

    if not mail_username or not mail_password:
        return False, "Las credenciales de correo (RESEND_API_KEY o MAIL_USERNAME/MAIL_PASSWORD) no están configuradas en el archivo .env"

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = mail_sender
        msg['To'] = to_email

        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')

        msg.attach(part1)
        msg.attach(part2)

        if mail_use_ssl:
            with smtplib.SMTP_SSL(mail_server, mail_port, timeout=15) as server:
                server.login(mail_username, mail_password)
                server.sendmail(mail_sender, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(mail_server, mail_port, timeout=15) as server:
                if mail_use_tls:
                    server.starttls()
                server.login(mail_username, mail_password)
                server.sendmail(mail_sender, [to_email], msg.as_string())

        return True, f"Correo enviado exitosamente a {to_email}"

    except smtplib.SMTPAuthenticationError:
        return False, "Error de autenticación SMTP: Verifica tu usuario y contraseña (o contraseña de aplicación si usas Gmail) en el archivo .env"
    except Exception as ex:
        return False, f"Error al enviar el correo: {str(ex)}"


def _dispatch_email(to_email: str, subject: str, text_content: str, html_content: str) -> tuple[bool, str]:
    """
    Enrutador inteligente de envío de correos:
    1. Si existe RESEND_API_KEY en variables de entorno, envía vía HTTPS (compatible con Render/Producción).
    2. De lo contrario, intenta por SMTP tradicional (Desarrollo local).
    """
    resend_api_key = config('RESEND_API_KEY', default='').strip()
    if resend_api_key:
        mail_sender = config('MAIL_DEFAULT_SENDER', default='OilSkin <onboarding@resend.dev>')
        return _send_via_resend(to_email, subject, text_content, html_content, resend_api_key, mail_sender)
    
    return _send_via_smtp(to_email, subject, text_content, html_content)


def send_password_reset_email(to_email: str, reset_url: str, user_name: str = "Usuario") -> tuple[bool, str]:
    """
    Envía un correo electrónico con diseño HTML responsivo para el restablecimiento de contraseña.
    """
    subject = "Restablece tu contraseña - OilSkin Cosmética Natural"

    text_content = f"""Hola {user_name},

Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en OilSkin.
Para definir tu nueva contraseña, ingresa al siguiente enlace (válido por 1 hora):

{reset_url}

Si no realizaste esta solicitud, puedes ignorar este mensaje de forma segura. Tu contraseña actual no cambiará.

Atentamente,
El equipo de OilSkin Cosmética Natural
"""

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0c0c0c; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #e5e5e5;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; background-color: #0c0c0c; padding: 40px 10px;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #141414; border: 1px solid #262626; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                    
                    <!-- Header -->
                    <tr>
                        <td align="center" style="background: linear-gradient(180deg, #1f1f1f 0%, #141414 100%); padding: 35px 30px 25px 30px; border-bottom: 1px solid #262626;">
                            <h1 style="margin: 0; color: #CEB06E; font-size: 26px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase;">OIL SKIN</h1>
                            <p style="margin: 6px 0 0 0; color: #a3a3a3; font-size: 12px; letter-spacing: 1px; text-transform: uppercase;">Cosmética Botánica & Cuidado Facial</p>
                        </td>
                    </tr>

                    <!-- Main Body -->
                    <tr>
                        <td style="padding: 35px 35px 25px 35px; text-align: left;">
                            <h2 style="margin: 0 0 16px 0; color: #ffffff; font-size: 20px; font-weight: 700;">Restablecimiento de Contraseña</h2>
                            <p style="margin: 0 0 16px 0; color: #d4d4d4; font-size: 15px; line-height: 1.6;">
                                Hola <strong style="color: #CEB06E;">{user_name}</strong>,
                            </p>
                            <p style="margin: 0 0 24px 0; color: #a3a3a3; font-size: 14px; line-height: 1.6;">
                                Recibimos una solicitud para restablecer la contraseña asociada a tu cuenta. Para continuar y definir tu nueva clave de acceso, haz clic en el siguiente botón:
                            </p>

                            <!-- CTA Button -->
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{reset_url}" target="_blank" style="display: inline-block; background-color: #CEB06E; color: #0c0c0c; font-size: 15px; font-weight: 700; text-decoration: none; padding: 14px 34px; border-radius: 12px; box-shadow: 0 4px 15px rgba(206, 176, 110, 0.3);">
                                            Restablecer mi Contraseña
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 24px 0 12px 0; color: #737373; font-size: 12px; line-height: 1.5;">
                                Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:
                            </p>
                            <p style="margin: 0 0 24px 0; word-break: break-all;">
                                <a href="{reset_url}" target="_blank" style="color: #CEB06E; font-size: 12px; text-decoration: underline;">{reset_url}</a>
                            </p>

                            <div style="background-color: #1a1a1a; border-left: 3px solid #CEB06E; padding: 12px 16px; border-radius: 6px; margin: 24px 0 10px 0;">
                                <p style="margin: 0; color: #a3a3a3; font-size: 12px; line-height: 1.5;">
                                    ⏰ <strong>Validez:</strong> Este enlace expirará en <strong>60 minutos</strong> por tu seguridad.
                                </p>
                            </div>

                            <p style="margin: 20px 0 0 0; color: #737373; font-size: 12px; line-height: 1.5;">
                                Si tú no solicitaste este cambio, no te preocupes: tu cuenta sigue protegida y puedes ignorar este correo.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td align="center" style="background-color: #0d0d0d; padding: 25px 30px; border-top: 1px solid #222222;">
                            <p style="margin: 0 0 8px 0; color: #737373; font-size: 11px;">
                                © 2026 OilSkin S.A.S. Todos los derechos reservados.
                            </p>
                            <p style="margin: 0; color: #525252; font-size: 10px;">
                                Este es un mensaje automático del sistema de autenticación de OilSkin. Por favor no respondas a este correo.
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    return _dispatch_email(to_email, subject, text_content, html_content)


def send_password_reset_otp(to_email: str, otp_code: str, user_name: str = "Cliente") -> tuple[bool, str]:
    """
    Envía un correo electrónico con un código numérico OTP de 6 dígitos para recuperación de contraseña.
    Diseñado con estética premium OilSkin (Dark Mode + Acentos Dorados).
    """
    subject = f"{otp_code} es tu código de recuperación - OilSkin"

    text_content = f"""Hola {user_name},

Tu código de verificación para restablecer tu contraseña en OilSkin es:

{otp_code}

Este código es válido durante 15 minutos. Por tu seguridad, nunca compartas este código con nadie.
Si tú no realizaste esta solicitud, puedes ignorar este mensaje de forma segura.

Atentamente,
El equipo de OilSkin Cosmética Natural
"""

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0c0c0c; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #e5e5e5;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; background-color: #0c0c0c; padding: 40px 10px;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 560px; background-color: #141414; border: 1px solid #262626; border-radius: 24px; overflow: hidden; box-shadow: 0 15px 35px rgba(0,0,0,0.6);">
                    
                    <!-- Header Corporativo -->
                    <tr>
                        <td align="center" style="background: linear-gradient(180deg, #1c1c1c 0%, #141414 100%); padding: 35px 30px 25px 30px; border-bottom: 1px solid #262626;">
                            <h1 style="margin: 0; color: #CEB06E; font-size: 26px; font-weight: 800; letter-spacing: 3px; text-transform: uppercase;">OIL SKIN</h1>
                            <p style="margin: 6px 0 0 0; color: #a3a3a3; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase;">Cosmética Botánica & Cuidado Facial</p>
                        </td>
                    </tr>

                    <!-- Contenido Principal -->
                    <tr>
                        <td style="padding: 35px 35px 25px 35px; text-align: left;">
                            <h2 style="margin: 0 0 16px 0; color: #ffffff; font-size: 20px; font-weight: 700;">Código de Verificación</h2>
                            <p style="margin: 0 0 16px 0; color: #d4d4d4; font-size: 15px; line-height: 1.6;">
                                Hola <strong style="color: #CEB06E;">{user_name}</strong>,
                            </p>
                            <p style="margin: 0 0 20px 0; color: #a3a3a3; font-size: 14px; line-height: 1.6;">
                                Recibimos una solicitud para restablecer la contraseña de tu cuenta. Ingresa el siguiente código numérico de 6 dígitos en la pantalla de verificación:
                            </p>

                            <!-- Caja Destacada del Código OTP -->
                            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin: 25px 0;">
                                <tr>
                                    <td align="center">
                                        <div style="display: inline-block; background-color: #1a1a1a; border: 2px dashed #CEB06E; border-radius: 18px; padding: 18px 36px; text-align: center; box-shadow: 0 6px 20px rgba(206, 176, 110, 0.15);">
                                            <span style="font-family: 'Courier New', Courier, monospace; font-size: 38px; font-weight: 800; letter-spacing: 10px; color: #CEB06E; display: block; margin-left: 10px;">{otp_code}</span>
                                            <span style="display: block; margin-top: 6px; color: #a3a3a3; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px;">Código de seguridad temporal</span>
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <!-- Alerta de Expiración y Seguridad -->
                            <div style="background-color: #1a1a1a; border-left: 3px solid #CEB06E; padding: 14px 18px; border-radius: 8px; margin: 24px 0 15px 0;">
                                <p style="margin: 0; color: #d4d4d4; font-size: 13px; line-height: 1.5;">
                                    ⏰ <strong>Validez:</strong> Este código expira en <strong>15 minutos</strong>.
                                </p>
                                <p style="margin: 6px 0 0 0; color: #737373; font-size: 12px; line-height: 1.4;">
                                    Por motivos de seguridad, se invalidará tras 5 intentos erróneos. Nunca compartas este código con nadie.
                                </p>
                            </div>

                            <p style="margin: 20px 0 0 0; color: #737373; font-size: 12px; line-height: 1.5;">
                                Si no solicitaste restablecer tu contraseña, puedes ignorar este mensaje: tu cuenta sigue segura y no se realizará ningún cambio.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td align="center" style="padding: 20px 30px; background-color: #0f0f0f; border-top: 1px solid #1f1f1f; color: #525252; font-size: 11px;">
                            © OilSkin Cosmética Natural. Todos los derechos reservados.
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    return _dispatch_email(to_email, subject, text_content, html_content)

