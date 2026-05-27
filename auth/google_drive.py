"""
auth/google_drive.py
Operaciones con Google Drive usando autenticación OAuth2.
"""

import json
import os

try:
    import requests as _req
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from config import CREDENTIALS_FILE
from auth.oauth import obtener_credenciales, credenciales_json_validas

_DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"


def _token() -> str:
    """Obtiene un access token OAuth2 válido."""
    from google.auth.transport.requests import Request
    creds = obtener_credenciales()
    if not creds.valid:
        creds.refresh(Request())
    return creds.token


def subir_pdf(pdf_bytes: bytes, nombre_archivo: str, folder_id: str = "") -> dict:
    """Sube un PDF a Google Drive y lo hace público (anyone with link)."""
    if not REQUESTS_AVAILABLE:
        raise ImportError("Instala: pip install requests")

    token    = _token()
    BOUNDARY = "pdf_boundary_xZ9m"

    meta = {"name": nombre_archivo, "mimeType": "application/pdf"}
    if folder_id:
        meta["parents"] = [folder_id]

    cuerpo = (
        f"--{BOUNDARY}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
    ).encode() + json.dumps(meta).encode() + (
        f"\r\n--{BOUNDARY}\r\nContent-Type: application/pdf\r\n\r\n"
    ).encode() + pdf_bytes + f"\r\n--{BOUNDARY}--".encode()

    resp = _req.post(
        "https://www.googleapis.com/upload/drive/v3/files"
        "?uploadType=multipart&fields=id,webViewLink",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  f"multipart/related; boundary={BOUNDARY}",
        },
        data=cuerpo,
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Error subiendo a Drive ({resp.status_code}): {resp.text[:300]}")

    file_data = resp.json()
    _hacer_publico(file_data["id"], token)
    return file_data


def _hacer_publico(file_id: str, token: str) -> None:
    try:
        _req.post(
            f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": "reader", "type": "anyone"},
            timeout=30,
        )
    except Exception:
        pass


def obtener_email_bot() -> str:
    """Para OAuth2 no hay 'email del bot' — retorna estado de autorización."""
    from auth.oauth import obtener_info_estado
    info = obtener_info_estado()
    return info["estado_txt"]


def credenciales_validas() -> bool:
    """Verifica que credentials.json es un archivo OAuth2 válido."""
    return credenciales_json_validas()