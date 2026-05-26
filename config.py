"""
config.py — Configuración central del sistema.
Edita este archivo para adaptar el proyecto a tu hoja de cálculo.
"""

# ── Nombres de columnas en Google Sheets ──────────────────────────────────
# Deben coincidir EXACTAMENTE con los encabezados de tu hoja (sensible a mayúsculas).
COLUMN_CONFIG: dict[str, str] = {
    "nombre":   "Nombre",
    "apellido": "Apellido",           # ← columna de apellido(s)
    "empresa":  "Empresa",
    "email":    "Email",
    "folio":    "Número de Folio",
    "fecha":    "Timestamp",          # columna de fecha del Google Form
    "estado":   "Estado",             # columna de control; se crea si no existe
}

# ── Google Drive — carpeta temporal para conversión a PDF ────────────────────
# Crea una carpeta en TU Google Drive personal, compártela con el email de la
# cuenta de servicio (rol Editor) y pega aquí el ID de la carpeta.
# El ID está en la URL: drive.google.com/drive/folders/<FOLDER_ID>
# Si se deja vacío, sube al Drive de la cuenta de servicio (cuota limitada).
DRIVE_FOLDER_ID: str = ""   # ← pega aquí el ID de tu carpeta compartida

# ── Rutas de archivos ─────────────────────────────────────────────────────
CREDENTIALS_FILE: str = "credentials.json"               # cuenta de servicio de Google
TEMPLATE_FILE:    str = "plantilla_constancia.png"       # plantilla PNG con <<MARCADORES>>
OUTPUT_FOLDER:    str = "constancias_generadas"           # carpeta de salida

# ── Google API ────────────────────────────────────────────────────────────
GOOGLE_SCOPES: list[str] = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"       # completo: sube y borra temporales para PDF,
]

# ── Control de envío ──────────────────────────────────────────────────────
BATCH_SIZE:   int   = 100   # máximo de correos por lote
EMAIL_DELAY:  float = 1.5   # segundos de pausa entre correos (anti-spam)

# ── Paleta de colores de la interfaz ──────────────────────────────────────
COLOR: dict[str, str] = {
    "bg_oscuro":    "#1E2533",
    "bg_panel":     "#252D3D",
    "bg_input":     "#2E3A50",
    "acento":       "#4A90D9",
    "acento_hover": "#6AAEF0",
    "exito":        "#27AE60",
    "advertencia":  "#F39C12",
    "error":        "#E74C3C",
    "texto":        "#ECF0F1",
    "texto_dim":    "#95A5A6",
    "borde":        "#3A4A63",
    "listo":        "#2ECC71",
    "enviado":      "#3498DB",
    "fallido":      "#E74C3C",
}
