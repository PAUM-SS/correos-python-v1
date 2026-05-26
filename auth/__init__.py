"""auth/ — Autenticación y operaciones con Google Sheets."""
from .google_sheets import (
    conectar_google_sheets,
    obtener_registros_con_folio,
    marcar_enviado_en_sheet,
)

__all__ = [
    "conectar_google_sheets",
    "obtener_registros_con_folio",
    "marcar_enviado_en_sheet",
]
