"""
config_manager.py
Lee y escribe 'settings.json' en la raíz del proyecto.
"""

import json
import os
import copy

SETTINGS_FILE = "settings.json"

DEFAULTS: dict = {
    "credenciales": {
        "remitente":  "",
        "contrasena": "",
    },
    "sheets": {
        "spreadsheet_id": "",
    },
    "columnas": {
        "nombre":   "Nombres",
        "apellido": "Apellidos",
        "email":    "Correo electrónico de contacto (Asegúrese de que sea una dirección activa)",
        "folio":    "Folio",
        "fecha":    "Marca temporal",
    },
    "sesion": {
        "ponencia": "",
        "ponente":  "",
        "fecha":    "",
    },
    "email_cuerpo": {
        "asunto": "Constancia de Participación — Folio {folio}",
        "html":   (
            "<p>Estimado/a <b>{nombre} {apellido}</b>,</p>"
            "<p>Adjunto encontrará su constancia de participación "
            "con el folio <b>{folio}</b>.</p>"
            "<p>Si tiene alguna pregunta, no dude en contactarnos.</p>"
            "<p>Atentamente,<br><b>La Sociedad Mexicana de Anatomía A.C.</b></p>"
        ),
    },
    "drive": {
        "folder_id": "",
    },
    "general": {
        "batch_size":      100,
        "email_delay":     1.5,
        "template_file":   "plantilla_constancia.png",
        "output_folder":   "constancias_generadas",
        "filename_campo":  "folio",
        "filename_sufijo": "",
    },
}


def cargar_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        return copy.deepcopy(DEFAULTS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            guardado = json.load(f)
    except (json.JSONDecodeError, OSError):
        return copy.deepcopy(DEFAULTS)

    resultado = copy.deepcopy(DEFAULTS)
    for seccion, valores in guardado.items():
        if seccion in resultado and isinstance(valores, dict):
            resultado[seccion].update(valores)
        else:
            resultado[seccion] = valores
    return resultado


def guardar_settings(settings: dict) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def aplicar_settings(settings: dict) -> None:
    """Propaga los settings a los módulos activos."""
    import config

    columnas = settings.get("columnas", {})
    config.COLUMN_CONFIG.clear()
    config.COLUMN_CONFIG.update(columnas)

    general = settings.get("general", {})
    if "batch_size"    in general: config.BATCH_SIZE    = int(general["batch_size"])
    if "email_delay"   in general: config.EMAIL_DELAY   = float(general["email_delay"])
    if "template_file" in general: config.TEMPLATE_FILE = general["template_file"]
    if "output_folder" in general: config.OUTPUT_FOLDER = general["output_folder"]

    sesion = settings.get("sesion", {})
    try:
        from templates import SESION_CONFIG
        SESION_CONFIG.update(sesion)
    except Exception:
        pass
