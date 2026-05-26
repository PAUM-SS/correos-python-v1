"""templates/ — Generación de constancias PDF sobre plantilla PNG con Pillow."""
from .image_builder import generar_constancia, generar_preview, generar_nombre_archivo, SESION_CONFIG

generar_constancia_pptx  = generar_constancia
limpiar_temporales_drive = lambda: (0, "Método PNG activo — sin Drive.")

__all__ = [
    "generar_constancia",
    "generar_constancia_pptx",
    "generar_preview",
    "generar_nombre_archivo",
    "limpiar_temporales_drive",
    "SESION_CONFIG",
]
