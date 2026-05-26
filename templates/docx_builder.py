# """
# templates/docx_builder.py
# Genera archivos .docx personalizados a partir de una plantilla Word con
# marcadores {{CLAVE}} para cada campo de datos.

# PLANTILLA REQUERIDA: 'plantilla_constancia.docx' en la raíz del proyecto.
# Marcadores disponibles: {{NOMBRE}}, {{EMPRESA}}, {{FOLIO}}, {{EMAIL}}, {{FECHA}}

# PREREQ:
#     pip install python-docx
# """

# import io
# import os
# import datetime

# try:
#     from docx import Document
#     DOCX_AVAILABLE = True
# except ImportError:
#     DOCX_AVAILABLE = False

# from config import TEMPLATE_FILE, OUTPUT_FOLDER, COLUMN_CONFIG


# # ─────────────────────────────────────────────────────────────────────────────
# #  API PÚBLICA
# # ─────────────────────────────────────────────────────────────────────────────

# def generar_constancia_docx(datos_fila: dict) -> bytes:
#     """
#     Genera un .docx personalizado en memoria (y lo guarda en disco).

#     Toma la plantilla, reemplaza todos los marcadores {{CLAVE}} con los
#     valores de 'datos_fila' y retorna los bytes resultantes listos para
#     adjuntarse a un correo.

#     Args:
#         datos_fila: dict con los datos de una fila de Google Sheets.
#                     Las claves son los encabezados de la hoja.

#     Returns:
#         bytes del documento .docx generado.

#     Raises:
#         ImportError:       si python-docx no está instalado.
#         FileNotFoundError: si la plantilla no existe en la ruta configurada.
#     """
#     if not DOCX_AVAILABLE:
#         raise ImportError(
#             "python-docx no está instalado.\n"
#             "Instala con: pip install python-docx"
#         )

#     if not os.path.exists(TEMPLATE_FILE):
#         raise FileNotFoundError(
#             f"No se encontró la plantilla '{TEMPLATE_FILE}'.\n"
#             "Crea un archivo Word con marcadores: "
#             "{{NOMBRE}}, {{EMPRESA}}, {{FOLIO}}, {{EMAIL}}, {{FECHA}}"
#         )

#     doc = Document(TEMPLATE_FILE)
#     marcadores = _construir_marcadores(datos_fila)

#     _reemplazar_en_documento(doc, marcadores)

#     # Guardar copia en disco para registro
#     _guardar_en_disco(doc, marcadores["FOLIO"])

#     # Retornar bytes para adjuntar al correo
#     return _documento_a_bytes(doc)


# # ─────────────────────────────────────────────────────────────────────────────
# #  HELPERS PRIVADOS
# # ─────────────────────────────────────────────────────────────────────────────

# def _construir_marcadores(datos_fila: dict) -> dict[str, str]:
#     """
#     Mapea los datos de la fila al diccionario de marcadores del template.
#     Agrega {{FECHA}} generada automáticamente.
#     """
#     fecha_str = datetime.datetime.now().strftime("%d de %B de %Y")
#     return {
#         "NOMBRE":  str(datos_fila.get(COLUMN_CONFIG["nombre"],  "")),
#         "EMPRESA": str(datos_fila.get(COLUMN_CONFIG["empresa"], "")),
#         "FOLIO":   str(datos_fila.get(COLUMN_CONFIG["folio"],   "")),
#         "EMAIL":   str(datos_fila.get(COLUMN_CONFIG["email"],   "")),
#         "FECHA":   fecha_str,
#     }


# def _reemplazar_en_documento(doc, marcadores: dict[str, str]) -> None:
#     """
#     Reemplaza marcadores en todos los párrafos del cuerpo y en tablas,
#     preservando el formato original de cada run de Word.
#     """
#     # Párrafos del cuerpo principal
#     for parrafo in doc.paragraphs:
#         _reemplazar_en_parrafo(parrafo, marcadores)

#     # Celdas de tablas (si la plantilla usa tablas)
#     for tabla in doc.tables:
#         for fila_tabla in tabla.rows:
#             for celda in fila_tabla.cells:
#                 for parrafo in celda.paragraphs:
#                     _reemplazar_en_parrafo(parrafo, marcadores)


# def _reemplazar_en_parrafo(parrafo, marcadores: dict[str, str]) -> None:
#     """
#     Itera los runs de un párrafo y reemplaza {{CLAVE}} → valor.
#     Operar a nivel de run preserva negrita, cursiva, tamaño de fuente, etc.
#     """
#     for run in parrafo.runs:
#         for clave, valor in marcadores.items():
#             placeholder = "{{" + clave + "}}"
#             if placeholder in run.text:
#                 run.text = run.text.replace(placeholder, valor)


# def _guardar_en_disco(doc, folio: str) -> str:
#     """
#     Guarda el documento en OUTPUT_FOLDER con nombre Constancia_<FOLIO>.docx.
#     Retorna la ruta completa del archivo guardado.
#     """
#     os.makedirs(OUTPUT_FOLDER, exist_ok=True)
#     folio_safe = folio.replace("/", "-").replace("\\", "-")
#     ruta = os.path.join(OUTPUT_FOLDER, f"Constancia_{folio_safe}.docx")
#     doc.save(ruta)
#     return ruta


# def _documento_a_bytes(doc) -> bytes:
#     """Serializa el documento a bytes en memoria."""
#     buffer = io.BytesIO()
#     doc.save(buffer)
#     buffer.seek(0)
#     return buffer.read()
