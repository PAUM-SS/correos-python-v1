"""
send/email_sender.py
Envío de correos con adjunto PDF y cuerpo HTML enriquecido.
Soporte para variables {nombre}, {apellido}, {folio} en asunto y cuerpo.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email                import encoders

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

_ASUNTO_DEFAULT = "Constancia de Participación — Folio {folio}"
_HTML_DEFAULT   = (
    "<p>Estimado/a <b>{nombre} {apellido}</b>,</p>"
    "<p>Adjunto encontrará su constancia con el folio <b>{folio}</b>.</p>"
    "<p>Atentamente,<br><b>La Sociedad Mexicana de Anatomía A.C.</b></p>"
)


def enviar_correo(
    remitente:       str,
    contrasena:      str,
    destinatario:    str,
    nombre:          str,
    apellido:        str,
    folio:           str,
    archivo_adjunto: bytes,
    nombre_archivo:  str  = "Constancia.pdf",
    asunto_tpl:      str  = _ASUNTO_DEFAULT,
    html_tpl:        str  = _HTML_DEFAULT,
) -> None:
    """
    Envía la constancia en PDF con cuerpo HTML.

    Las plantillas de asunto y cuerpo admiten:
      {nombre}, {apellido}, {folio}
    """
    ctx = {"nombre": nombre, "apellido": apellido, "folio": folio}

    asunto = asunto_tpl.format_map(_SafeDict(ctx))
    html   = html_tpl.format_map(_SafeDict(ctx))

    msg = MIMEMultipart("mixed")
    msg["From"]    = remitente
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
    nombre_safe = nombre_archivo.replace('"', '')
    parte.add_header("Content-Disposition", f'attachment; filename="{nombre_safe}"')
    msg.attach(parte)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as srv:
        srv.ehlo(); srv.starttls(); srv.login(remitente, contrasena)
        srv.sendmail(remitente, destinatario, msg.as_string())


class _SafeDict(dict):
    """Permite format_map sin KeyError si una clave no está definida."""
    def __missing__(self, key):
        return f"{{{key}}}"
