"""
auth/google_sheets.py
Operaciones con Google Sheets usando autenticación OAuth2.
"""

import os
import datetime

try:
    import gspread
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

from config import CREDENTIALS_FILE, GOOGLE_SCOPES, COLUMN_CONFIG
from auth.oauth import obtener_credenciales

COL_DOC_GENERADO  = "Documento Generado"
COL_LINK_DRIVE    = "Link Drive"
COL_CORREO_ESTADO = "Correo Enviado"
COL_FOLIO_SESION  = "Folio Sesion"


# ─────────────────────────────────────────────────────────────────────────────
#  CONEXIÓN
# ─────────────────────────────────────────────────────────────────────────────

def conectar_google_sheets(spreadsheet_id: str):
    """
    Conecta a Google Sheets usando credenciales OAuth2.
    Si no hay token guardado, abre el navegador para autorizar.
    """
    if not GSPREAD_AVAILABLE:
        raise ImportError("Instala: pip install gspread")

    creds   = obtener_credenciales()
    cliente = gspread.authorize(creds)
    return cliente.open_by_key(spreadsheet_id).sheet1


# ─────────────────────────────────────────────────────────────────────────────
#  VALIDACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def folio_es_valido(folio) -> bool:
    valor = str(folio).strip()
    return bool(valor) and "/" not in valor


def verificar_columnas(worksheet) -> dict:
    encabezados = worksheet.row_values(1)
    encontradas, faltantes = {}, {}
    for clave, nombre in COLUMN_CONFIG.items():
        (encontradas if nombre in encabezados else faltantes)[clave] = nombre
    return {"encabezados": encabezados, "encontradas": encontradas, "faltantes": faltantes}


# ─────────────────────────────────────────────────────────────────────────────
#  LECTURA
# ─────────────────────────────────────────────────────────────────────────────

def obtener_registros_con_folio(worksheet) -> tuple[list[dict], dict]:
    """
    Retorna TODOS los registros con al menos una celda no vacía.
    numericise_ignore=['all'] evita que gspread convierta "0001052026" → 1052026.
    """
    reporte = verificar_columnas(worksheet)
    todos   = worksheet.get_all_records(numericise_ignore=['all'])

    filtrados = []
    for fila in todos:
        if not any(str(v).strip() for v in fila.values()):
            continue

        estado_envio = str(fila.get(COL_CORREO_ESTADO, "")).strip()
        fila["_estado_local"] = "enviado" if estado_envio.lower().startswith("enviado") else "listo"
        filtrados.append(fila)

    return filtrados, reporte


# ─────────────────────────────────────────────────────────────────────────────
#  ESCRITURA DE SEGUIMIENTO
# ─────────────────────────────────────────────────────────────────────────────

def _ts() -> str:
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M")


def _fila_de_folio(worksheet, folio: str) -> int | None:
    col_folio   = COLUMN_CONFIG.get("folio", "Folio")
    encabezados = worksheet.row_values(1)
    if col_folio not in encabezados:
        return None
    idx   = encabezados.index(col_folio) + 1
    vals  = worksheet.col_values(idx)
    for i, val in enumerate(vals[1:], start=2):
        if str(val).strip() == str(folio).strip():
            return i
    return None


def _asegurar_columna(worksheet, nombre: str) -> int:
    encabezados = worksheet.row_values(1)
    if nombre in encabezados:
        return encabezados.index(nombre) + 1
    idx = len(encabezados) + 1
    worksheet.update_cell(1, idx, nombre)
    return idx


def registrar_documento_generado(worksheet, folio: str) -> None:
    try:
        fila = _fila_de_folio(worksheet, folio)
        if fila:
            worksheet.update_cell(fila, _asegurar_columna(worksheet, COL_DOC_GENERADO), f"Sí - {_ts()}")
    except Exception:
        pass


def registrar_link_drive(worksheet, folio: str, link: str) -> None:
    try:
        fila = _fila_de_folio(worksheet, folio)
        if fila:
            worksheet.update_cell(fila, _asegurar_columna(worksheet, COL_LINK_DRIVE), link)
    except Exception:
        pass


def registrar_estado_envio(worksheet, folio: str, enviado: bool) -> None:
    try:
        fila = _fila_de_folio(worksheet, folio)
        if fila:
            valor = f"{'Enviado' if enviado else 'Fallido'} - {_ts()}"
            worksheet.update_cell(fila, _asegurar_columna(worksheet, COL_CORREO_ESTADO), valor)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  GENERACIÓN DE FOLIOS SESIÓN
# ─────────────────────────────────────────────────────────────────────────────

def generar_folios_sesion(worksheet) -> int:
    """
    Escribe folios en la columna 'Folio Sesion' con formato 0001MMAAAA.
    Usa value_input_option=RAW para preservar ceros iniciales.
    No sobreescribe filas que ya tienen folio.
    """
    import datetime
    import gspread

    encabezados = worksheet.row_values(1)
    if COL_FOLIO_SESION not in encabezados:
        nueva_col = len(encabezados) + 1
        worksheet.update_cell(1, nueva_col, COL_FOLIO_SESION)
        encabezados.append(COL_FOLIO_SESION)

    idx_col   = encabezados.index(COL_FOLIO_SESION) + 1
    mes_anio  = datetime.datetime.now().strftime("%m%Y")
    col_letra = gspread.utils.rowcol_to_a1(1, idx_col)[:-1]
    col_actual = worksheet.col_values(idx_col)
    todos      = worksheet.get_all_records(numericise_ignore=['all'])

    updates = []
    for i, fila in enumerate(todos, start=1):
        fila_hoja    = i + 1
        valor_actual = col_actual[fila_hoja - 1] if fila_hoja <= len(col_actual) else ""
        if str(valor_actual).strip():
            continue
        folio = f"{str(i).zfill(4)}{mes_anio}"
        updates.append({"range": f"{col_letra}{fila_hoja}", "values": [[folio]]})

    if updates:
        worksheet.spreadsheet.values_batch_update({
            "valueInputOption": "RAW",
            "data": updates,
        })

    return len(updates)