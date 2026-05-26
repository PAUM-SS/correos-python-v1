"""
send/email_sender.py
Encapsula el envío de correos a través de Gmail usando SMTP con TLS.

SETUP (Gmail):
    1. Activa la Verificación en 2 pasos en tu cuenta de Google.
    2. Ve a myaccount.google.com → Seguridad → Contraseñas de aplicaciones.
    3. Genera una contraseña para "Correo / Otra aplicación" (16 caracteres).
    4. Usa ESA contraseña en el campo de la app, NO tu contraseña normal.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTES SMTP
# ─────────────────────────────────────────────────────────────────────────────

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


# ─────────────────────────────────────────────────────────────────────────────
#  FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def enviar_correo(
    remitente:    str,
    contrasena:   str,
    destinatario: str,
    nombre:       str,
    folio:        str,
    archivo_adjunto: bytes,
) -> None:
    """
    Envía un correo con la constancia adjunta en formato .pdf.

    Args:
        remitente:    dirección Gmail del emisor.
        contrasena:   contraseña de aplicación de Google (16 caracteres).
        destinatario: email del destinatario.
        nombre:       nombre completo del destinatario (para el saludo).
        folio:        número de folio (para asunto y nombre del adjunto).
        archivo_docx: bytes del .docx generado por docx_builder.

    Raises:
        smtplib.SMTPAuthenticationError: si las credenciales son incorrectas.
        smtplib.SMTPRecipientsRefused:   si el email destino es inválido.
        smtplib.SMTPException:           cualquier otro error de transporte.
        ConnectionRefusedError:          sin acceso a internet o SMTP bloqueado.
    """
    msg = _construir_mensaje(remitente, destinatario, nombre, folio, archivo_adjunto)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
        servidor.ehlo()
        servidor.starttls()                          # cifrado TLS obligatorio
        servidor.login(remitente, contrasena)
        servidor.sendmail(remitente, destinatario, msg.as_string())


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS PRIVADOS
# ─────────────────────────────────────────────────────────────────────────────

def _construir_mensaje(
    remitente:    str,
    destinatario: str,
    nombre:       str,
    folio:        str,
    archivo_adjunto: bytes,
) -> MIMEMultipart:
    """Ensambla el objeto MIME con cuerpo de texto y adjunto .docx."""

    msg = MIMEMultipart()
    msg["From"]    = remitente
    msg["To"]      = destinatario
    msg["Subject"] = f"Constancia de Participación — Folio {folio}"

    cuerpo = _cuerpo_correo(nombre, folio)
    msg.attach(MIMEText(cuerpo, "plain", "utf-8"))

    adjunto = _construir_adjunto(archivo_adjunto, folio)
    msg.attach(adjunto)

    return msg


def _cuerpo_correo(nombre: str, folio: str) -> str:
    """Retorna el texto plano del cuerpo del correo."""
    return (
        f"Estimado/a {nombre},\n\n"
        f"Adjunto encontrará su constancia de participación con el folio {folio}.\n\n"
        "Si tiene alguna pregunta, no dude en contactarnos.\n\n"
        "Atentamente,\n"
        "Departamento de Recursos Humanos"
    )


def _construir_adjunto(archivo_adjunto: bytes, folio: str) -> MIMEBase:
    """Crea el objeto MIME para el adjunto .docx con codificación base64."""
    folio_safe = str(folio).replace("/", "-").replace("\\", "-")
    nombre_archivo = f"Constancia_{folio_safe}.pdf"

    parte = MIMEBase("application", "pdf")
    parte.set_payload(archivo_adjunto)
    encoders.encode_base64(parte)
    parte.add_header("Content-Disposition", f'attachment; filename="{nombre_archivo}"')
    return parte