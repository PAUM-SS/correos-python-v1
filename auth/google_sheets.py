"""
auth/google_sheets.py
Maneja autenticación con Google Sheets y operaciones de lectura/escritura.

Columnas de seguimiento que se crean automáticamente en la hoja:
  - "Documento Generado" : timestamp de cuando se generó el PDF
  - "Link Drive"         : URL directa al archivo en Drive
  - "Correo Enviado"     : "Enviado DD/MM/YYYY HH:MM" o "Fallido ..."

La columna "Correo Enviado" se usa para deduplicación:
  si ya dice "Enviado...", esa fila no se procesa de nuevo.
"""

import os
import datetime

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

from config import CREDENTIALS_FILE, GOOGLE_SCOPES, COLUMN_CONFIG

# Nombres fijos de las columnas de seguimiento (no configurables)
COL_DOC_GENERADO  = "Documento Generado"
COL_LINK_DRIVE    = "Link Drive"
COL_CORREO_ESTADO = "Correo Enviado"


# ─────────────────────────────────────────────────────────────────────────────
#  AUTENTICACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def conectar_google_sheets(spreadsheet_id: str):
    if not GSPREAD_AVAILABLE:
        raise ImportError("Instala: pip install gspread google-auth")
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"No se encontró '{CREDENTIALS_FILE}'.\n"
            "Descárgalo desde Google Cloud Console → Cuenta de Servicio → JSON."
        )
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=GOOGLE_SCOPES)
    cliente = gspread.authorize(creds)
    return cliente.open_by_key(spreadsheet_id).sheet1


# ─────────────────────────────────────────────────────────────────────────────
#  VALIDACIÓN DE FOLIO
# ─────────────────────────────────────────────────────────────────────────────

def folio_es_valido(folio) -> bool:
    """
    Folio inválido si está vacío o contiene '/'.
    Descarta n/a, N/A, N/a, etc. automáticamente.
    """
    valor = str(folio).strip()
    return bool(valor) and "/" not in valor


# ─────────────────────────────────────────────────────────────────────────────
#  VERIFICACIÓN DE ENCABEZADOS
# ─────────────────────────────────────────────────────────────────────────────

def verificar_columnas(worksheet) -> dict:
    encabezados = worksheet.row_values(1)
    encontradas, faltantes = {}, {}
    for clave, nombre in COLUMN_CONFIG.items():
        (encontradas if nombre in encabezados else faltantes)[clave] = nombre
    return {"encabezados": encabezados, "encontradas": encontradas, "faltantes": faltantes}


# ─────────────────────────────────────────────────────────────────────────────
#  LECTURA CON DEDUPLICACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def obtener_registros_con_folio(worksheet) -> tuple[list[dict], dict]:
    """
    Descarga TODOS los registros con al menos una celda no vacía.
    No filtra por folio — se envían constancias a todas las personas.
    Marca como 'enviado' las filas donde COL_CORREO_ESTADO ya dice "Enviado"
    (deduplicación: no se reenvían constancias ya procesadas).
    Retorna (registros, reporte_columnas).
    """
    reporte = verificar_columnas(worksheet)
    todos   = worksheet.get_all_records(numericise_ignore=['all'])

    filtrados = []
    for fila in todos:
        # Saltar filas completamente vacías
        if not any(str(v).strip() for v in fila.values()):
            continue

        estado_envio = str(fila.get(COL_CORREO_ESTADO, "")).strip()
        if estado_envio.lower().startswith("enviado"):
            fila["_estado_local"] = "enviado"
        else:
            fila["_estado_local"] = "listo"

        filtrados.append(fila)

    return filtrados, reporte


# ─────────────────────────────────────────────────────────────────────────────
#  ESCRITURA DE SEGUIMIENTO
# ─────────────────────────────────────────────────────────────────────────────

def _fila_de_folio(worksheet, folio: str) -> int | None:
    """Retorna el número de fila (1-indexed) donde está el folio, o None."""
    col_folio   = COLUMN_CONFIG["folio"]
    encabezados = worksheet.row_values(1)
    if col_folio not in encabezados:
        return None
    idx_folio = encabezados.index(col_folio) + 1
    col_vals  = worksheet.col_values(idx_folio)
    for i, val in enumerate(col_vals[1:], start=2):  # skip header
        if str(val).strip() == str(folio).strip():
            return i
    return None


def _asegurar_columna(worksheet, nombre_col: str) -> int:
    """
    Si la columna no existe, la crea al final.
    Retorna el índice de columna (1-indexed).
    """
    encabezados = worksheet.row_values(1)
    if nombre_col in encabezados:
        return encabezados.index(nombre_col) + 1
    nuevo_idx = len(encabezados) + 1
    worksheet.update_cell(1, nuevo_idx, nombre_col)
    return nuevo_idx


def _ts() -> str:
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M")


def registrar_documento_generado(worksheet, folio: str) -> None:
    """Escribe timestamp en 'Documento Generado' para la fila del folio."""
    try:
        fila = _fila_de_folio(worksheet, folio)
        if not fila:
            return
        idx = _asegurar_columna(worksheet, COL_DOC_GENERADO)
        worksheet.update_cell(fila, idx, f"Sí - {_ts()}")
    except Exception:
        pass


def registrar_link_drive(worksheet, folio: str, link: str) -> None:
    """Escribe el link de Drive en 'Link Drive' para la fila del folio."""
    try:
        fila = _fila_de_folio(worksheet, folio)
        if not fila:
            return
        idx = _asegurar_columna(worksheet, COL_LINK_DRIVE)
        worksheet.update_cell(fila, idx, link)
    except Exception:
        pass


def registrar_estado_envio(worksheet, folio: str, enviado: bool) -> None:
    """
    Escribe en 'Correo Enviado':
      - "Enviado DD/MM/YYYY HH:MM"  si enviado=True
      - "Fallido DD/MM/YYYY HH:MM"  si enviado=False
    """
    try:
        fila = _fila_de_folio(worksheet, folio)
        if not fila:
            return
        idx   = _asegurar_columna(worksheet, COL_CORREO_ESTADO)
        valor = f"{'Enviado' if enviado else 'Fallido'} - {_ts()}"
        worksheet.update_cell(fila, idx, valor)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  GENERACIÓN DE FOLIOS SESIÓN
# ─────────────────────────────────────────────────────────────────────────────

COL_FOLIO_SESION = "Folio Sesion"


def generar_folios_sesion(worksheet) -> int:
    """
    Crea o actualiza la columna 'Folio Sesion' en la hoja.

    Formato: {índice_4_dígitos}{mes_2_dígitos}{año_4_dígitos}
    Ej: fila 1 → "0001052025",  fila 2 → "0002052025",  etc.

    Los valores se escriben como texto (value_input_option=RAW) para
    que Google Sheets NO convierta "0001052025" al número 1052025.

    Las filas que ya tienen folio asignado no se sobreescriben.
    Usa batch update: una sola llamada API para todas las filas.

    Returns:
        Número de folios escritos.
    """
    import datetime
    import gspread

    encabezados = worksheet.row_values(1)

    # Crear la columna si no existe
    if COL_FOLIO_SESION not in encabezados:
        nueva_col = len(encabezados) + 1
        worksheet.update_cell(1, nueva_col, COL_FOLIO_SESION)
        encabezados.append(COL_FOLIO_SESION)

    idx_col  = encabezados.index(COL_FOLIO_SESION) + 1    # 1-indexed
    mes_anio = datetime.datetime.now().strftime("%m%Y")    # "052025"

    # Letra de la columna (A, B, C... Z, AA, etc.)
    col_letra  = gspread.utils.rowcol_to_a1(1, idx_col)[:-1]
    col_actual = worksheet.col_values(idx_col)             # incluye encabezado
    todos      = worksheet.get_all_records(numericise_ignore=['all'])

    # Construir lista de actualizaciones (no sobreescribir existentes)
    updates = []
    for i, fila in enumerate(todos, start=1):
        fila_hoja    = i + 1                               # +1 por encabezado
        valor_actual = col_actual[fila_hoja - 1] if fila_hoja <= len(col_actual) else ""
        if str(valor_actual).strip():
            continue                                        # ya tiene folio

        folio = f"{str(i).zfill(4)}{mes_anio}"            # "0001052025"
        updates.append({
            "range":  f"{col_letra}{fila_hoja}",
            "values": [[folio]],
        })

    if not updates:
        return 0

    # Batch update con RAW → los strings se guardan tal cual, sin conversión numérica
    worksheet.spreadsheet.values_batch_update({
        "valueInputOption": "RAW",
        "data": updates,
    })

    return len(updates)