# """
# templates/pptx_builder.py
# Genera constancias en PDF a partir de la plantilla .pptx.

# MÉTODO DE CONVERSIÓN — elige uno en CONVERSION_METHOD:

#   "spire"   → spire.presentation  (pip install Spire.Presentation)
#               ✅ Cross-platform  ✅ Sin sistema  ⚠ Marca de agua en versión gratis
#               Instalar: pip install Spire.Presentation

#   "soffice" → LibreOffice headless  (requiere instalación del sistema)
#               ✅ Mejor calidad  ✅ Sin costo  ⚠ Requiere LibreOffice instalado
#               Linux:   sudo apt install libreoffice
#               Windows: descargar de libreoffice.org

#   "drive"   → Google Drive API  (requiere carpeta compartida con la SA)
#               ✅ Sin instalación local  ⚠ Requiere DRIVE_FOLDER_ID en config.py
# """

# import io
# import os
# import subprocess
# import tempfile

# try:
#     from pptx import Presentation
#     PPTX_AVAILABLE = True
# except ImportError:
#     PPTX_AVAILABLE = False

# from config import TEMPLATE_FILE, OUTPUT_FOLDER, COLUMN_CONFIG, CREDENTIALS_FILE

# # ── Elige el método de conversión ────────────────────────────────────────────
# # Opciones: "spire" | "soffice" | "drive"
# CONVERSION_METHOD: str = "spire"


# # ─────────────────────────────────────────────────────────────────────────────
# #  CONFIGURACIÓN DE SESIÓN
# # ─────────────────────────────────────────────────────────────────────────────

# SESION_CONFIG: dict[str, str] = {
#     "ponencia": "",
#     "ponente":  "",
#     "fecha":    "",
# }


# # ─────────────────────────────────────────────────────────────────────────────
# #  API PÚBLICA
# # ─────────────────────────────────────────────────────────────────────────────

# def generar_constancia_pptx(datos_fila: dict) -> bytes:
#     """
#     Genera la constancia en PDF.
#     Usa el método configurado en CONVERSION_METHOD.
#     """
#     if not PPTX_AVAILABLE:
#         raise ImportError("Instala python-pptx:  pip install python-pptx")
#     if not os.path.exists(TEMPLATE_FILE):
#         raise FileNotFoundError(f"No se encontró la plantilla '{TEMPLATE_FILE}'.")

#     reemplazos = _mapa_reemplazos(datos_fila)
#     pptx_bytes = _generar_pptx_bytes(reemplazos)
#     pdf_bytes  = _convertir_a_pdf(pptx_bytes)

#     _guardar_pdf_en_disco(pdf_bytes, datos_fila)
#     return pdf_bytes


# def limpiar_temporales_drive() -> tuple[int, str]:
#     """Stub para compatibilidad cuando el método no es 'drive'."""
#     if CONVERSION_METHOD == "drive":
#         return _limpiar_drive()
#     return 0, f"Método '{CONVERSION_METHOD}' activo — no hay temporales de Drive."


# # ─────────────────────────────────────────────────────────────────────────────
# #  REEMPLAZO DE MARCADORES  (python-pptx)
# # ─────────────────────────────────────────────────────────────────────────────

# def _mapa_reemplazos(datos_fila: dict) -> dict[str, str]:
#     return {
#         "<<Nombre(s)>>":    str(datos_fila.get(COLUMN_CONFIG["nombre"],   "")),
#         "<<Apellido(s)>>":  str(datos_fila.get(COLUMN_CONFIG["apellido"], "")),
#         "<<Folio sesion>>": str(datos_fila.get(COLUMN_CONFIG["folio"],    "")),
#         "<<Ponencia>>":     SESION_CONFIG["ponencia"],
#         "<<Ponente>>":      SESION_CONFIG["ponente"],
#         "<<Fecha>>":        SESION_CONFIG["fecha"],
#     }


# def _generar_pptx_bytes(reemplazos: dict[str, str]) -> bytes:
#     """Carga la plantilla, reemplaza marcadores y retorna bytes del PPTX."""
#     prs = Presentation(TEMPLATE_FILE)
#     for slide in prs.slides:
#         for shape in slide.shapes:
#             if not shape.has_text_frame:
#                 continue
#             for paragraph in shape.text_frame.paragraphs:
#                 for run in paragraph.runs:
#                     texto = run.text
#                     for marcador, valor in reemplazos.items():
#                         if marcador in texto:
#                             texto = texto.replace(marcador, valor)
#                     run.text = texto
#     buf = io.BytesIO()
#     prs.save(buf)
#     buf.seek(0)
#     return buf.read()


# # ─────────────────────────────────────────────────────────────────────────────
# #  CONVERSIÓN — despachador
# # ─────────────────────────────────────────────────────────────────────────────

# def _convertir_a_pdf(pptx_bytes: bytes) -> bytes:
#     if CONVERSION_METHOD == "spire":
#         return _convertir_spire(pptx_bytes)
#     if CONVERSION_METHOD == "soffice":
#         return _convertir_soffice(pptx_bytes)
#     if CONVERSION_METHOD == "drive":
#         return _convertir_drive(pptx_bytes)
#     raise ValueError(
#         f"CONVERSION_METHOD='{CONVERSION_METHOD}' no reconocido. "
#         "Usa 'spire', 'soffice' o 'drive'."
#     )


# # ── Método 1: spire.presentation ─────────────────────────────────────────────

# def _convertir_spire(pptx_bytes: bytes) -> bytes:
#     """
#     Convierte a PDF usando spire.presentation.
#     Instalar: pip install Spire.Presentation
#     Nota: versión gratuita agrega "Evaluation Warning" en la diapositiva.
#           Licencia comercial en: https://www.e-iceblue.com
#     """
#     try:
#         from spire.presentation import Presentation as SpirePrs, FileFormat
#     except ImportError:
#         raise ImportError(
#             "spire.presentation no instalado.\n"
#             "Instala con: pip install Spire.Presentation"
#         )

#     with tempfile.TemporaryDirectory() as tmpdir:
#         pptx_path = os.path.join(tmpdir, "entrada.pptx")
#         pdf_path  = os.path.join(tmpdir, "salida.pdf")

#         with open(pptx_path, "wb") as f:
#             f.write(pptx_bytes)

#         prs = SpirePrs()
#         prs.LoadFromFile(pptx_path)
#         prs.SaveToFile(pdf_path, FileFormat.PDF)
#         prs.Dispose()

#         with open(pdf_path, "rb") as f:
#             return f.read()


# # ── Método 2: LibreOffice headless ───────────────────────────────────────────

# def _convertir_soffice(pptx_bytes: bytes) -> bytes:
#     """
#     Convierte a PDF usando LibreOffice headless.
#     Linux:   sudo apt install libreoffice
#     Windows: https://www.libreoffice.org/download/download-libreoffice/
#     """
#     ejecutable = _encontrar_soffice()

#     with tempfile.TemporaryDirectory() as tmpdir:
#         pptx_path = os.path.join(tmpdir, "entrada.pptx")
#         pdf_path  = os.path.join(tmpdir, "entrada.pdf")

#         with open(pptx_path, "wb") as f:
#             f.write(pptx_bytes)

#         result = subprocess.run(
#             [ejecutable, "--headless", "--convert-to", "pdf",
#              "--outdir", tmpdir, pptx_path],
#             capture_output=True,
#             timeout=60,
#         )
#         if result.returncode != 0 or not os.path.exists(pdf_path):
#             raise RuntimeError(
#                 f"LibreOffice falló: {result.stderr.decode(errors='replace')}"
#             )

#         with open(pdf_path, "rb") as f:
#             return f.read()


# def _encontrar_soffice() -> str:
#     """Localiza soffice/libreoffice en el PATH."""
#     import shutil
#     for nombre in ("soffice", "libreoffice"):
#         ruta = shutil.which(nombre)
#         if ruta:
#             return ruta
#     raise RuntimeError(
#         "LibreOffice no encontrado.\n"
#         "Linux:   sudo apt install libreoffice\n"
#         "Windows: https://www.libreoffice.org/download/"
#     )


# # ── Método 3: Google Drive API ───────────────────────────────────────────────

# def _convertir_drive(pptx_bytes: bytes) -> bytes:
#     """
#     Convierte a PDF usando Google Drive API.
#     Requiere DRIVE_FOLDER_ID en config.py y google-auth + requests instalados.
#     """
#     try:
#         import json, time
#         import requests as _req
#         from google.oauth2.service_account import Credentials
#         from google.auth.transport.requests import Request as GReq
#     except ImportError:
#         raise ImportError("Instala: pip install google-auth requests")

#     try:
#         from config import DRIVE_FOLDER_ID
#     except ImportError:
#         DRIVE_FOLDER_ID = ""

#     SCOPE    = "https://www.googleapis.com/auth/drive"
#     BOUNDARY = "constancia_bnd_xK9mZ"
#     NOMBRE   = "_constancia_temporal_"

#     creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=[SCOPE])
#     creds.refresh(GReq())
#     token = creds.token

#     meta = {"name": NOMBRE, "mimeType": "application/vnd.google-apps.presentation"}
#     if DRIVE_FOLDER_ID:
#         meta["parents"] = [DRIVE_FOLDER_ID]

#     cuerpo = (
#         f"--{BOUNDARY}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
#     ).encode() + json.dumps(meta).encode() + (
#         f"\r\n--{BOUNDARY}\r\nContent-Type: application/vnd.openxmlformats-officedocument"
#         ".presentationml.presentation\r\n\r\n"
#     ).encode() + pptx_bytes + f"\r\n--{BOUNDARY}--".encode()

#     r = _req.post(
#         "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id",
#         headers={"Authorization": f"Bearer {token}",
#                  "Content-Type": f"multipart/related; boundary={BOUNDARY}"},
#         data=cuerpo, timeout=120,
#     )
#     if r.status_code != 200:
#         raise RuntimeError(f"Error al subir a Drive ({r.status_code}): {r.text[:400]}")

#     fid = r.json()["id"]
#     try:
#         for _ in range(3):
#             ex = _req.get(
#                 f"https://www.googleapis.com/drive/v3/files/{fid}/export",
#                 params={"mimeType": "application/pdf"},
#                 headers={"Authorization": f"Bearer {token}"}, timeout=60,
#             )
#             if ex.status_code == 200:
#                 return ex.content
#             time.sleep(2)
#         raise RuntimeError(f"Drive no pudo exportar el PDF ({ex.status_code}): {ex.text[:200]}")
#     finally:
#         _req.delete(
#             f"https://www.googleapis.com/drive/v3/files/{fid}",
#             headers={"Authorization": f"Bearer {token}"}, timeout=30,
#         )


# def _limpiar_drive() -> tuple[int, str]:
#     try:
#         import requests as _req
#         from google.oauth2.service_account import Credentials
#         from google.auth.transport.requests import Request as GReq
#         SCOPE = "https://www.googleapis.com/auth/drive"
#         creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=[SCOPE])
#         creds.refresh(GReq())
#         token = creds.token
#         r = _req.get(
#             "https://www.googleapis.com/drive/v3/files",
#             params={"q": "name='_constancia_temporal_'", "fields": "files(id)"},
#             headers={"Authorization": f"Bearer {token}"}, timeout=30,
#         )
#         ids = [f["id"] for f in r.json().get("files", [])] if r.status_code == 200 else []
#         for fid in ids:
#             _req.delete(f"https://www.googleapis.com/drive/v3/files/{fid}",
#                         headers={"Authorization": f"Bearer {token}"}, timeout=30)
#         _req.delete("https://www.googleapis.com/drive/v3/files/trash",
#                     headers={"Authorization": f"Bearer {token}"}, timeout=30)
#         msg = f"{len(ids)} archivos eliminados y papelera vaciada." if ids else "Papelera vaciada."
#         return len(ids), msg
#     except Exception as e:
#         return 0, f"Error limpiando Drive: {e}"


# # ─────────────────────────────────────────────────────────────────────────────
# #  GUARDADO EN DISCO
# # ─────────────────────────────────────────────────────────────────────────────

# def _guardar_pdf_en_disco(pdf_bytes: bytes, datos_fila: dict) -> str:
#     os.makedirs(OUTPUT_FOLDER, exist_ok=True)
#     folio    = str(datos_fila.get(COLUMN_CONFIG["folio"],    "SIN_FOLIO"))
#     apellido = str(datos_fila.get(COLUMN_CONFIG["apellido"], ""))
#     nombre   = str(datos_fila.get(COLUMN_CONFIG["nombre"],   ""))
#     folio_safe = folio.replace("/", "-").replace("\\", "-").replace(" ", "_")
#     ruta = os.path.join(OUTPUT_FOLDER, f"Constancia_{folio_safe}_{apellido}_{nombre}.pdf")
#     with open(ruta, "wb") as f:
#         f.write(pdf_bytes)
#     return ruta
