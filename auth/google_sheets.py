"""
auth/google_sheets.py
Maneja la autenticación con la API de Google y todas las operaciones
de lectura/escritura sobre Google Sheets.

PREREQS:
    pip install gspread google-auth

SETUP:
    1. Habilita Google Sheets API y Google Drive API en Google Cloud Console.
    2. Crea una Cuenta de Servicio y descarga el JSON como 'credentials.json'.
    3. Comparte la hoja con el email de la Cuenta de Servicio
       (nombre@proyecto.iam.gserviceaccount.com) dándole rol Editor.
"""

import os

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

from config import CREDENTIALS_FILE, GOOGLE_SCOPES, COLUMN_CONFIG



# ─────────────────────────────────────────────────────────────────────────────
#  AUTENTICACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def conectar_google_sheets(spreadsheet_id: str):
    """
    Autentica con la Cuenta de Servicio y retorna el primer worksheet.

    Args:
        spreadsheet_id: ID de la hoja (parte de la URL entre /d/ y /edit).

    Returns:
        gspread.Worksheet: hoja de trabajo activa.

    Raises:
        ImportError:        si gspread / google-auth no están instalados.
        FileNotFoundError:  si credentials.json no existe en la raíz del proyecto.
        gspread.exceptions.APIError: si el ID es inválido o faltan permisos.
    """
    if not GSPREAD_AVAILABLE:
        raise ImportError(
            "Librerías de Google no disponibles.\n"
            "Instala con: pip install gspread google-auth"
        )

    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"No se encontró '{CREDENTIALS_FILE}'.\n"
            "Descárgalo desde Google Cloud Console → Cuenta de Servicio → JSON."
        )

    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=GOOGLE_SCOPES)
    cliente = gspread.authorize(creds)
    spreadsheet = cliente.open_by_key(spreadsheet_id)

    # Retorna la primera hoja; cambia a .worksheet("NombreHoja") si es otra.
    return spreadsheet.sheet1


# ─────────────────────────────────────────────────────────────────────────────
#  DIAGNÓSTICO DE ENCABEZADOS
# ─────────────────────────────────────────────────────────────────────────────

def obtener_encabezados(worksheet) -> list[str]:
    """
    Retorna los encabezados reales de la hoja (fila 1).
    Úsalo para verificar que COLUMN_CONFIG coincide con tu hoja real.
    """
    return worksheet.row_values(1)


def verificar_columnas(worksheet) -> dict:
    """
    Compara los nombres en COLUMN_CONFIG contra los encabezados reales.

    Returns:
        dict con:
            "encabezados"  : lista de encabezados reales de la hoja
            "encontradas"  : {clave_config: nombre_columna}  — columnas que SÍ coinciden
            "faltantes"    : {clave_config: nombre_buscado}  — columnas que NO se encontraron
    """
    encabezados_reales = obtener_encabezados(worksheet)
    encontradas = {}
    faltantes   = {}

    for clave, nombre_columna in COLUMN_CONFIG.items():
        if nombre_columna in encabezados_reales:
            encontradas[clave] = nombre_columna
        else:
            faltantes[clave] = nombre_columna

    return {
        "encabezados": encabezados_reales,
        "encontradas": encontradas,
        "faltantes":   faltantes,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  LECTURA DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

def folio_es_valido(folio: str) -> bool:
    """
    Determina si un folio es válido para generar constancia.

    Regla: un folio es INVÁLIDO si está vacío o contiene el carácter '/'.
    Esto descarta automáticamente todas las variantes de "n/a":
      n/a · N/a · N/A · n/A · etc.

    Args:
        folio: valor del campo folio tal como viene de la hoja.

    Returns:
        True si el folio es válido, False si debe omitirse.
    """
    valor = str(folio).strip()
    if not valor:
        return False          # vacío
    if "/" in valor:
        return False          # n/a, N/A, N/a, 01/2026, etc.
    return True


def obtener_registros_con_folio(worksheet) -> tuple[list[dict], dict]:
    """
    Descarga todos los registros y filtra los que tienen un folio válido.

    Un folio es INVÁLIDO si está vacío o contiene '/'.
    Esto descarta todas las variantes de "n/a" (n/a, N/A, N/a…)
    sin importar mayúsculas o minúsculas.

    Args:
        worksheet: objeto gspread.Worksheet activo.

    Returns:
        Tupla (registros_filtrados, reporte_columnas):
            - registros_filtrados: lista de dicts con filas que tienen folio válido
            - reporte_columnas:    resultado de verificar_columnas() para diagnóstico
    """
    reporte   = verificar_columnas(worksheet)
    col_folio = COLUMN_CONFIG["folio"]
    todos     = worksheet.get_all_records()

    filtrados = [
        fila for fila in todos
        if folio_es_valido(fila.get(col_folio, ""))
    ]

    return filtrados, reporte


# ─────────────────────────────────────────────────────────────────────────────
#  ESCRITURA DE ESTADO
# ─────────────────────────────────────────────────────────────────────────────

def marcar_enviado_en_sheet(worksheet, folio: str, estado: str = "Enviado") -> None:
    """
    Localiza la fila con el folio indicado y actualiza la columna 'Estado'.
    Si la columna no existe, la crea al final de los encabezados.

    Args:
        worksheet: objeto gspread.Worksheet activo.
        folio:     número de folio a buscar.
        estado:    texto a escribir en la columna Estado (default: "Enviado").
    """
    col_folio  = COLUMN_CONFIG["folio"]
    col_estado = COLUMN_CONFIG["estado"]

    encabezados = worksheet.row_values(1)

    # Crear columna Estado si no existe
    if col_estado not in encabezados:
        siguiente_col = len(encabezados) + 1
        worksheet.update_cell(1, siguiente_col, col_estado)
        encabezados.append(col_estado)

    idx_estado = encabezados.index(col_estado) + 1   # gspread usa índices 1-based

    registros = worksheet.get_all_records()
    for i, fila in enumerate(registros, start=2):     # fila 1 = encabezados
        if str(fila.get(col_folio, "")).strip() == str(folio).strip():
            worksheet.update_cell(i, idx_estado, estado)
            return