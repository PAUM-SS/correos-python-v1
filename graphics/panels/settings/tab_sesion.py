"""
graphics/panels/settings/tab_sesion.py
Pestaña 📋 Sesión: ponencia, ponente y fecha del evento.
Datos fijos para todo el lote actual.
"""

import tkinter as tk
from tkinter import ttk

from config import COLOR


class TabSesion(tk.Frame):

    def __init__(self, padre, vars_: dict):
        super().__init__(padre, bg=COLOR["bg_panel"], padx=16, pady=14)
        self._vars = vars_
        self._construir()

    def _construir(self):
        C = COLOR
        self.columnconfigure(0, weight=1)

        tk.Label(
            self,
            text=(
                "Datos fijos para todo el lote actual.\n"
                "Se insertan en los campos <<Ponencia>>, <<Ponente>>, <<Fecha>>."
            ),
            bg=C["bg_panel"], fg=C["texto_dim"],
            font=("Segoe UI", 8), justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        campos = [
            ("ponencia", "Ponencia / Tema:"),
            ("ponente",  "Ponente:"),
            ("fecha",    "Fecha del evento:"),
        ]
        for i, (clave, etiqueta) in enumerate(campos):
            row = 1 + i * 2
            ttk.Label(self, text=etiqueta).grid(row=row, column=0, sticky="w", pady=(8 if i > 0 else 0, 2))
            ttk.Entry(self, textvariable=self._vars[clave], width=50).grid(
                row=row + 1, column=0, sticky="ew")

    def recoger(self) -> dict:
        return {k: self._vars[k].get().strip() for k in ("ponencia", "ponente", "fecha")}
