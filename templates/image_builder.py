"""
templates/image_builder.py
Genera constancias en PDF pintando texto sobre la plantilla PNG con Pillow.

FLUJO:
  1. Abre la plantilla PNG (TEMPLATE_FILE en config.py → debe ser un .png)
  2. Borra las áreas de los marcadores con un rectángulo blanco
  3. Escribe el texto real con la fuente, color y posición correctas
  4. Exporta como PDF (Pillow lo hace directamente, sin dependencias externas)

PREREQS:
    pip install Pillow

CALIBRACIÓN:
    Si el texto no queda bien posicionado, ajusta los valores en CAMPOS abajo.
    Coordenadas en píxeles absolutas para una imagen de 2250 × 3000 px.
    Llama a generar_preview() para generar un PNG de prueba antes de enviar.
"""

import io
import os
import shutil

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from config import TEMPLATE_FILE, OUTPUT_FOLDER, COLUMN_CONFIG

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACIÓN DE SESIÓN — datos fijos para todo el lote
# ─────────────────────────────────────────────────────────────────────────────

SESION_CONFIG: dict[str, str] = {
    "ponencia": "",
    "ponente":  "",
    "fecha":    "",
}

# ─────────────────────────────────────────────────────────────────────────────
#  DEFINICIÓN DE CAMPOS
#  Calibrado para la plantilla 2250 × 3000 px.
#  Si cambias de plantilla, ajusta erase_box y pos.
# ─────────────────────────────────────────────────────────────────────────────

CAMPOS = {
    "folio": {
        # Rectángulo a borrar (x_ini, y_ini, x_fin, y_fin)
        "erase_box": (1680, 28, 2250, 88),
        # Posición del texto: (x, y)
        "pos":       (2220, 40),
        # Alineación Pillow: "ra" = right-ascender (alineado derecha, arriba)
        "anchor":    "ra",
        # Color RGB exacto del texto original
        "color":     (22, 52, 81),
        # Tamaño de fuente en píxeles
        "font_size": 36,
        # Tipo de fuente: "mono" | "bold" | "regular"
        "font_type": "mono",
        # Texto a renderizar: función lambda que recibe datos_fila
        "texto_fn":  lambda d: str(d.get(COLUMN_CONFIG["folio"], "")),
    },
    "nombre_apellido": {
        "erase_box": (140, 1238, 2110, 1425),
        "pos":       (1125, 1334),
        "anchor":    "mm",                     # mm = middle-middle (centrado)
        "color":     (0, 111, 198),
        "font_size": 132,
        "font_type": "bold",
        "texto_fn":  lambda d: (
            f"{d.get(COLUMN_CONFIG['nombre'], '')} "
            f"{d.get(COLUMN_CONFIG['apellido'], '')}"
        ).strip(),
    },
}


# ─────────────────────────────────────────────────────────────────────────────
#  API PÚBLICA
# ─────────────────────────────────────────────────────────────────────────────

def generar_constancia(datos_fila: dict) -> bytes:
    """
    Genera la constancia en PDF.

    Args:
        datos_fila: dict con los datos de una fila de Google Sheets.

    Returns:
        bytes del PDF generado (también guardado en OUTPUT_FOLDER).

    Raises:
        ImportError:       si Pillow no está instalado.
        FileNotFoundError: si la plantilla PNG no existe.
    """
    _verificar()

    img    = Image.open(TEMPLATE_FILE).convert("RGB")
    draw   = ImageDraw.Draw(img)
    fuente_cache: dict[str, ImageFont.FreeTypeFont] = {}

    for nombre_campo, cfg in CAMPOS.items():
        texto = cfg["texto_fn"](datos_fila).strip()
        if not texto:
            continue

        # 1. Borrar área del marcador
        draw.rectangle(cfg["erase_box"], fill=(255, 255, 255))

        # 2. Cargar fuente (con caché para no recargar en cada campo)
        cache_key = f"{cfg['font_type']}_{cfg['font_size']}"
        if cache_key not in fuente_cache:
            fuente_cache[cache_key] = _cargar_fuente(cfg["font_type"], cfg["font_size"])

        # 3. Dibujar texto
        draw.text(
            cfg["pos"],
            texto,
            font=fuente_cache[cache_key],
            fill=cfg["color"],
            anchor=cfg["anchor"],
        )

    pdf_bytes = _imagen_a_pdf(img)
    _guardar_en_disco(pdf_bytes, datos_fila)
    return pdf_bytes


def generar_preview(datos_fila: dict | None = None, ruta_salida: str = "preview_constancia.png") -> str:
    """
    Genera un PNG de previsualización para verificar posicionamiento.
    Útil para calibrar CAMPOS sin necesidad de enviar correos.

    Args:
        datos_fila: datos de prueba; si None, usa datos de ejemplo.
        ruta_salida: ruta donde guardar el PNG de preview.

    Returns:
        Ruta del archivo generado.
    """
    _verificar()
    if datos_fila is None:
        datos_fila = {
            COLUMN_CONFIG["nombre"]:   "Juan Carlos",
            COLUMN_CONFIG["apellido"]: "García López",
            COLUMN_CONFIG["folio"]:    "N-0053",
        }

    img  = Image.open(TEMPLATE_FILE).convert("RGB")
    draw = ImageDraw.Draw(img)

    for cfg in CAMPOS.values():
        texto = cfg["texto_fn"](datos_fila).strip()
        if not texto:
            continue
        draw.rectangle(cfg["erase_box"], fill=(255, 255, 255))
        fuente = _cargar_fuente(cfg["font_type"], cfg["font_size"])
        draw.text(cfg["pos"], texto, font=fuente, fill=cfg["color"], anchor=cfg["anchor"])

    # Guardar como PNG reducido para revisión rápida
    preview = img.resize((img.width // 4, img.height // 4), Image.LANCZOS)
    preview.save(ruta_salida)
    return ruta_salida


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS PRIVADOS
# ─────────────────────────────────────────────────────────────────────────────

def _cargar_fuente(tipo: str, tamaño: int) -> ImageFont.FreeTypeFont:
    """
    Carga la fuente más adecuada disponible en el sistema.
    Funciona en Windows y Linux sin instalación adicional.
    """
    candidatos = {
        "bold": [
            "arialbd.ttf",              # Windows
            "Arial Bold.ttf",
            "LiberationSans-Bold.ttf",  # Linux
            "DejaVuSans-Bold.ttf",      # Linux fallback
        ],
        "mono": [
            "cour.ttf",                         # Windows
            "CourierNew.ttf",
            "LiberationMono-Regular.ttf",       # Linux
            "DejaVuSansMono.ttf",               # Linux fallback
        ],
        "regular": [
            "arial.ttf",
            "Arial.ttf",
            "LiberationSans-Regular.ttf",
            "DejaVuSans.ttf",
        ],
    }

    for nombre in candidatos.get(tipo, candidatos["regular"]):
        try:
            return ImageFont.truetype(nombre, tamaño)
        except (IOError, OSError):
            pass

    # Último recurso: fuente bitmap de Pillow
    return ImageFont.load_default(size=tamaño)


def _imagen_a_pdf(img: Image.Image) -> bytes:
    """Serializa la imagen RGB como PDF en memoria."""
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=150)
    buf.seek(0)
    return buf.read()


def _guardar_en_disco(pdf_bytes: bytes, datos_fila: dict) -> str:
    """Guarda el PDF en OUTPUT_FOLDER."""
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    folio    = str(datos_fila.get(COLUMN_CONFIG["folio"],    "SIN_FOLIO"))
    apellido = str(datos_fila.get(COLUMN_CONFIG["apellido"], ""))
    nombre   = str(datos_fila.get(COLUMN_CONFIG["nombre"],   ""))
    folio_s  = folio.replace("/", "-").replace("\\", "-").replace(" ", "_")
    ruta     = os.path.join(OUTPUT_FOLDER, f"Constancia_{folio_s}_{apellido}_{nombre}.pdf")
    with open(ruta, "wb") as f:
        f.write(pdf_bytes)
    return ruta


def _verificar() -> None:
    if not PILLOW_AVAILABLE:
        raise ImportError("Instala Pillow:  pip install Pillow")
    if not os.path.exists(TEMPLATE_FILE):
        raise FileNotFoundError(
            f"No se encontró la plantilla '{TEMPLATE_FILE}'.\n"
            "Asegúrate de que config.py → TEMPLATE_FILE apunte a tu .png"
        )