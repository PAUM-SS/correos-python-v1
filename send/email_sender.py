"""
send/email_sender.py
Envío de correos usando la Gmail API con OAuth2.
No requiere contraseña de aplicación — usa el token OAuth activo.

El remitente es automáticamente la cuenta de Google autorizada ("me").
Requiere scope: https://www.googleapis.com/auth/gmail.send

PREREQS:
    pip install google-auth-oauthlib google-auth requests
    Habilitar Gmail API en Google Cloud Console.
"""

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email                import encoders

try:
    import requests as _req
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

_GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

_ASUNTO_DEFAULT = "Constancia de Participación — Folio {folio}"
_HTML_DEFAULT   = (
    "<p>Estimado/a <b>{nombre} {apellido}</b>,</p>"
    "<p>Adjunto encontrará su constancia con el folio <b>{folio}</b>.</p>"
    "<p>Atentamente,<br><b>La Sociedad Mexicana de Anatomía A.C.</b></p>"
)


def enviar_correo(
    destinatario:    str,
    nombre:          str,
    apellido:        str,
    folio:           str,
    archivo_adjunto: bytes,
    nombre_archivo:  str = "Constancia.pdf",
    asunto_tpl:      str = _ASUNTO_DEFAULT,
    html_tpl:        str = _HTML_DEFAULT,
) -> None:
    """
    Envía la constancia en PDF usando la Gmail API (OAuth2).

    El token se obtiene automáticamente desde auth/oauth.py.
    El remitente es la cuenta de Google que autorizó la aplicación.

    Args:
        destinatario:    email del destinatario.
        nombre:          nombre del destinatario (para sustituir en la plantilla).
        apellido:        apellido del destinatario.
        folio:           número de folio (para sustituir en la plantilla).
        archivo_adjunto: bytes del PDF.
        nombre_archivo:  nombre del adjunto (con .pdf).
        asunto_tpl:      plantilla del asunto con variables {nombre}, {apellido}, {folio}.
        html_tpl:        plantilla HTML del cuerpo con las mismas variables.

    Raises:
        ImportError:  si requests no está instalado.
        RuntimeError: si la Gmail API rechaza el envío.
    """
    if not REQUESTS_AVAILABLE:
        raise ImportError("Instala: pip install requests")

    token  = _obtener_token()
    msg    = _construir_mensaje(destinatario, nombre, apellido, folio,
                                archivo_adjunto, nombre_archivo,
                                asunto_tpl, html_tpl)
    _enviar_via_api(token, msg)


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS PRIVADOS
# ─────────────────────────────────────────────────────────────────────────────

def _obtener_token() -> str:
    """Obtiene el access token OAuth2 vigente."""
    from auth.oauth import obtener_credenciales
    from google.auth.transport.requests import Request
    creds = obtener_credenciales()
    if not creds.valid:
        creds.refresh(Request())
    return creds.token


def _construir_mensaje(
    destinatario: str,
    nombre: str, apellido: str, folio: str,
    archivo_adjunto: bytes, nombre_archivo: str,
    asunto_tpl: str, html_tpl: str,
) -> MIMEMultipart:
    """Ensambla el mensaje MIME con cuerpo HTML y adjunto PDF."""
    ctx    = {"nombre": nombre, "apellido": apellido, "folio": folio}
    asunto = asunto_tpl.format_map(_SafeDict(ctx))
    html   = html_tpl.format_map(_SafeDict(ctx))

    msg = MIMEMultipart("mixed")
    msg["To"]      = destinatario
    msg["Subject"] = asunto

    # Cuerpo HTML
    alternativa = MIMEMultipart("alternative")
    alternativa.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(alternativa)

    # Adjunto PDF
    parte = MIMEBase("application", "pdf")
    parte.set_payload(archivo_adjunto)
    encoders.encode_base64(parte)
    parte.add_header("Content-Disposition",
                     f'attachment; filename="{nombre_archivo.replace(chr(34), "")}"')
    msg.attach(parte)

    return msg


def _enviar_via_api(token: str, msg: MIMEMultipart) -> None:
    """Codifica el mensaje en base64 y lo envía via Gmail API."""
    raw  = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    resp = _req.post(
        _GMAIL_SEND_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={"raw": raw},
        timeout=60,
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(
            f"Gmail API error ({resp.status_code}): {resp.text[:300]}"
        )


class _SafeDict(dict):
    """Permite format_map sin KeyError si una clave no está definida."""
    def __missing__(self, key):
        return f"{{{key}}}"