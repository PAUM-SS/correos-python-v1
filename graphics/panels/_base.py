"""
graphics/panels/_base.py
Clase base para todos los paneles del proyecto.
Implementa el patrón de "tarjeta" con título, separador y contenedor interior.
Los paneles hijos solo construyen su contenido dentro de self.contenedor.
"""

import tkinter as tk
from tkinter import ttk

from config import COLOR


class PanelBase(tk.Frame):
    """
    Marco con estilo de tarjeta (borde + fondo de panel + título + separador).

    Atributos:
        app:        referencia a la AplicacionConstancias (orquestador central).
        contenedor: tk.Frame interior donde los paneles hijos colocan sus widgets.
    """

    def __init__(self, padre, app, titulo: str = ""):
        C = COLOR
        # Marco exterior (sirve de borde de 1px)
        super().__init__(padre, bg=C["borde"], pady=1, padx=1)
        self.pack(fill="x", pady=(0, 8))

        self.app = app   # referencia al orquestador (AplicacionConstancias)

        # Marco interior (fondo de panel)
        interior = tk.Frame(self, bg=C["bg_panel"], padx=10, pady=8)
        interior.pack(fill="both")

        # Título de sección
        tk.Label(
            interior,
            text=titulo,
            bg=C["bg_panel"],
            fg=C["acento"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        ttk.Separator(interior, orient="horizontal").pack(fill="x", pady=(0, 4))

        # Contenedor donde los hijos añaden sus widgets
        self.contenedor = interior
