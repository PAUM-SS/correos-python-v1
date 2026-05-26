"""
auth/google_drive.py
Sube PDFs a Google Drive, obtiene links compartibles y consulta
datos de la cuenta de servicio.

Requiere scope: "https://www.googleapis.com/auth/drive"
"""

import io
import json
import os

try:
    import requests as _req
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import Request as GReq
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from config import CREDENTIALS_FILE

_DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"


# ─────────────────────────────────────────────────────────────────────────────
#  TOKEN
# ─────────────────────────────────────────────────────────────────────────────

def _token() -> str:
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=[_DRIVE_SCOPE])
    creds.refresh(GReq())
    return creds.token


# ─────────────────────────────────────────────────────────────────────────────
#  SUBIR PDF
# ─────────────────────────────────────────────────────────────────────────────

def subir_pdf(pdf_bytes: bytes, nombre_archivo: str, folder_id: str = "") -> dict:
    """
    Sube un PDF a Google Drive.

    Args:
        pdf_bytes:      bytes del archivo PDF.
        nombre_archivo: nombre con el que se guardará en Drive (incluye .pdf).
        folder_id:      ID de la carpeta destino. Si está vacío, se sube a My Drive.

    Returns:
        dict con claves 'id' y 'webViewLink'.

    Raises:
        RuntimeError: si la subida falla.
    """
    if not GOOGLE_AVAILABLE:
        raise ImportError("Instala: pip install google-auth requests")
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(f"No se encontró '{CREDENTIALS_FILE}'.")

    token = _token()
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
            "Content-Type": f"multipart/related; boundary={BOUNDARY}",
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
    """Permite ver el archivo a cualquiera con el link."""
    try:
        _req.post(
            f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": "reader", "type": "anyone"},
            timeout=30,
        )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  INFO DE LA CUENTA DE SERVICIO
# ─────────────────────────────────────────────────────────────────────────────

def obtener_email_bot() -> str:
    """Retorna el client_email de credentials.json."""
    if not os.path.exists(CREDENTIALS_FILE):
        return f"❌ '{CREDENTIALS_FILE}' no encontrado"
    try:
        with open(CREDENTIALS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("client_email", "client_email no encontrado en el JSON")
    except Exception as e:
        return f"Error leyendo credentials.json: {e}"


def credenciales_validas() -> bool:
    """Verifica que credentials.json existe y tiene el formato correcto."""
    if not os.path.exists(CREDENTIALS_FILE):
        return False
    try:
        with open(CREDENTIALS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("type") == "service_account" and "client_email" in data
    except Exception:
        return False
