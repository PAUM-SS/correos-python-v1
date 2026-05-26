"""auth/ — Autenticación y operaciones con Google Sheets y Drive."""
from .google_sheets import (
    conectar_google_sheets,
    obtener_registros_con_folio,
    folio_es_valido,
    registrar_documento_generado,
    registrar_link_drive,
    registrar_estado_envio,
)
from .google_drive import (
    subir_pdf,
    obtener_email_bot,
    credenciales_validas,
)

__all__ = [
    "conectar_google_sheets",
    "obtener_registros_con_folio",
    "folio_es_valido",
    "registrar_documento_generado",
    "registrar_link_drive",
    "registrar_estado_envio",
    "subir_pdf",
    "obtener_email_bot",
    "credenciales_validas",
]
