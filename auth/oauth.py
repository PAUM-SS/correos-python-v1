"""
auth/oauth.py
Gestión centralizada de credenciales OAuth2 con google-auth-oauthlib.

Diferencia con Cuenta de Servicio:
  - Cuenta de Servicio: un bot con su propio email, autenticación sin usuario.
  - OAuth2: el usuario autoriza con SU cuenta de Google directamente.

Flujo:
  1. Primera vez: abre el navegador → usuario acepta permisos → se guarda token.json
  2. Siguientes usos: lee token.json, lo refresca automáticamente si expiró.
  3. Si el refresh falla (token revocado): re-abre el navegador.

PREREQS:
    pip install google-auth-oauthlib google-auth gspread

ARCHIVO credentials.json esperado:
    Descargado de Google Cloud Console → Credenciales → OAuth 2.0 → Cliente de escritorio
    Formato: {"installed": {"client_id": "...", "client_secret": "...", ...}}
    NO es el JSON de Cuenta de Servicio.
"""

import json
import os
import threading

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials            import Credentials
    from google_auth_oauthlib.flow            import InstalledAppFlow
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False

from config import CREDENTIALS_FILE

TOKEN_FILE = "token.json"

# Scopes necesarios para Sheets + Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.send",   # envío de correos vía Gmail API
]


# ─────────────────────────────────────────────────────────────────────────────
#  OBTENCIÓN DE CREDENCIALES
# ─────────────────────────────────────────────────────────────────────────────

def obtener_credenciales() -> "Credentials":
    """
    Retorna credenciales OAuth2 válidas.

    Orden de prioridad:
      1. token.json válido → úsalo
      2. token.json expirado con refresh_token → refresca silenciosamente
      3. Sin token → abre navegador para autorizar (bloquea hasta que el
         usuario complete el flujo)

    Raises:
        ImportError:       si google-auth-oauthlib no está instalado.
        FileNotFoundError: si credentials.json no existe.
        Exception:         si el usuario cancela la autorización en el navegador.
    """
    if not OAUTH_AVAILABLE:
        raise ImportError(
            "Instala: pip install google-auth-oauthlib google-auth"
        )
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"No se encontró '{CREDENTIALS_FILE}'.\n"
            "Descárgalo de Google Cloud Console → Credenciales → "
            "OAuth 2.0 → Cliente de escritorio."
        )

    creds = _cargar_token()

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _guardar_token(creds)
            return creds
        except Exception:
            pass  # refresh falló → re-autorizar

    # Autorización interactiva (abre navegador)
    flow  = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    _guardar_token(creds)
    return creds


def autorizar_en_hilo(callback_ok, callback_err) -> None:
    """
    Lanza el flujo de autorización OAuth2 en un hilo separado para no
    bloquear la interfaz gráfica.

    Args:
        callback_ok(creds): llamado en el hilo principal si tuvo éxito.
        callback_err(str):  llamado en el hilo principal si falló.
    """
    def _tarea():
        try:
            creds = obtener_credenciales()
            callback_ok(creds)
        except Exception as e:
            callback_err(str(e))

    threading.Thread(target=_tarea, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
#  ESTADO
# ─────────────────────────────────────────────────────────────────────────────

def esta_autorizado() -> bool:
    """Retorna True si hay un token guardado (no verifica si está expirado)."""
    return os.path.exists(TOKEN_FILE)


def token_valido() -> bool:
    """Verifica que el token existe, no está expirado y tiene refresh_token."""
    creds = _cargar_token()
    if not creds:
        return False
    return creds.valid or bool(creds.refresh_token)


def revocar_token() -> None:
    """Elimina token.json forzando re-autorización en el siguiente uso."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)


def credenciales_json_validas() -> bool:
    """
    Verifica que credentials.json existe y tiene el formato OAuth2
    (debe tener clave 'installed' o 'web', NO 'type: service_account').
    """
    if not os.path.exists(CREDENTIALS_FILE):
        return False
    try:
        with open(CREDENTIALS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return "installed" in data or "web" in data
    except Exception:
        return False


def obtener_info_estado() -> dict:
    """
    Retorna un dict con información del estado de autenticación:
      - credentials_ok: bool
      - token_ok: bool
      - client_id: str  (del credentials.json)
      - estado_txt: str (texto para mostrar en UI)
    """
    info = {
        "credentials_ok": credenciales_json_validas(),
        "token_ok":        token_valido(),
        "client_id":       "",
        "estado_txt":      "",
    }

    if info["credentials_ok"]:
        try:
            with open(CREDENTIALS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            cfg = data.get("installed") or data.get("web") or {}
            info["client_id"] = cfg.get("client_id", "")
        except Exception:
            pass

    if not info["credentials_ok"]:
        info["estado_txt"] = "❌ credentials.json no encontrado o formato incorrecto"
    elif not info["token_ok"]:
        info["estado_txt"] = "⚠ No autorizado — presiona 'Autorizar con Google'"
    else:
        info["estado_txt"] = "✔ Autorizado correctamente"

    return info


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS PRIVADOS
# ─────────────────────────────────────────────────────────────────────────────

def _cargar_token() -> "Credentials | None":
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    except Exception:
        return None


def _guardar_token(creds: "Credentials") -> None:
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(creds.to_json())