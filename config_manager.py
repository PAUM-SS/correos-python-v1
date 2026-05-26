"""
config_manager.py
Lee y escribe 'settings.json' en la raíz del proyecto.
Centraliza la persistencia de toda la configuración de usuario:
  - Credenciales de correo (email + contraseña de aplicación)
  - Spreadsheet ID de Google Sheets
  - Nombres de columnas (COLUMN_CONFIG)
  - Datos de sesión (SESION_CONFIG)
  - Parámetros generales (lote, demora, rutas)

SEGURIDAD:
  La contraseña se guarda en texto plano en settings.json.
  Este archivo NO debe subirse a repositorios públicos.
  Añade 'settings.json' a tu .gitignore.
"""

import json
import os

SETTINGS_FILE = "settings.json"

# ─────────────────────────────────────────────────────────────────────────────
#  VALORES POR DEFECTO
# ─────────────────────────────────────────────────────────────────────────────

DEFAULTS: dict = {
    "credenciales": {
        "remitente":  "",
        "contrasena": "",
    },
    "sheets": {
        "spreadsheet_id": "",
    },
    "columnas": {
        "nombre":   "Nombre completo del solicitante",
        "apellido": "Apellido",
        "empresa":  "Empresa",
        "email":    "Correo electrónico de contacto (Asegúrese de que sea correcto)",
        "folio":    "Folio",
        "fecha":    "Marca temporal",
        "estado":   "Estado",
    },
    "sesion": {
        "ponencia": "",
        "ponente":  "",
        "fecha":    "",
    },
    "general": {
        "batch_size":    100,
        "email_delay":   1.5,
        "template_file": "plantilla_constancia.png",
        "output_folder": "constancias_generadas",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
#  LECTURA
# ─────────────────────────────────────────────────────────────────────────────

def cargar_settings() -> dict:
    """
    Lee settings.json y lo fusiona con los valores por defecto.
    Si el archivo no existe o está corrupto, retorna los defaults.
    """
    if not os.path.exists(SETTINGS_FILE):
        return _copia_defaults()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            guardado = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _copia_defaults()

    # Fusión profunda: defaults como base + valores guardados encima
    resultado = _copia_defaults()
    for seccion, valores in guardado.items():
        if seccion in resultado and isinstance(valores, dict):
            resultado[seccion].update(valores)
        else:
            resultado[seccion] = valores

    return resultado


# ─────────────────────────────────────────────────────────────────────────────
#  ESCRITURA
# ─────────────────────────────────────────────────────────────────────────────

def guardar_settings(settings: dict) -> None:
    """
    Escribe settings.json con los valores proporcionados.
    Crea el archivo si no existe.
    """
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
#  APLICACIÓN EN CALIENTE
# ─────────────────────────────────────────────────────────────────────────────

def aplicar_settings(settings: dict) -> None:
    """
    Propaga los settings cargados a los módulos de configuración activos.
    Llamar después de cargar o guardar settings.
    """
    import config

    # Columnas
    columnas = settings.get("columnas", {})
    config.COLUMN_CONFIG.update(columnas)

    # General
    general = settings.get("general", {})
    if "batch_size" in general:
        config.BATCH_SIZE = int(general["batch_size"])
    if "email_delay" in general:
        config.EMAIL_DELAY = float(general["email_delay"])
    if "template_file" in general:
        config.TEMPLATE_FILE = general["template_file"]
    if "output_folder" in general:
        config.OUTPUT_FOLDER = general["output_folder"]

    # Sesión → image_builder.SESION_CONFIG
    sesion = settings.get("sesion", {})
    try:
        from templates import SESION_CONFIG
        SESION_CONFIG.update(sesion)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _copia_defaults() -> dict:
    """Retorna una copia profunda de los valores por defecto."""
    import copy
    return copy.deepcopy(DEFAULTS)