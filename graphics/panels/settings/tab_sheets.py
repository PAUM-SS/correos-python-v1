"""
graphics/panels/settings/tab_sheets.py
Pestaña ☁ Google Sheets:
  - Spreadsheet ID
  - Nombres exactos de columnas (sin empresa ni estado)
  - Info sobre columnas de seguimiento automáticas
"""

import tkinter as tk
from tkinter import ttk

from config import COLOR
from auth.google_sheets import COL_DOC_GENERADO, COL_LINK_DRIVE, COL_CORREO_ESTADO


_COLUMNAS = [
    ("nombre",   "Nombre(s):"),
    ("apellido", "Apellido(s):"),
    ("email",    "Correo electrónico:"),
    ("folio",    "Número de Folio:"),
    ("fecha",    "Timestamp / Fecha:"),
]


class TabSheets(tk.Frame):

    def __init__(self, padre, vars_: dict):
        super().__init__(padre, bg=COLOR["bg_panel"], padx=16, pady=14)
        self._vars = vars_
        self._construir()

    def _construir(self):
        C = COLOR
        self.columnconfigure(0, weight=1)

        # ── Spreadsheet ID ────────────────────────────────────────────────
        ttk.Label(self, text="Spreadsheet ID:").grid(row=0, column=0, sticky="w")
        ttk.Entry(self, textvariable=self._vars["spreadsheet_id"], width=50).grid(
            row=1, column=0, sticky="ew", pady=(2, 0))
        ttk.Label(
            self,
            text="(Parte de la URL entre /d/ y /edit)",
            style="Sub.TLabel",
        ).grid(row=2, column=0, sticky="w", pady=(2, 0))

        ttk.Separator(self, orient="horizontal").grid(
            row=3, column=0, sticky="ew", pady=(12, 8))

        # ── Nombres de columnas ───────────────────────────────────────────
        tk.Label(self, text="Nombres exactos de columnas en la hoja:",
                 bg=C["bg_panel"], fg=C["acento"],
                 font=("Segoe UI", 9, "bold")).grid(
            row=4, column=0, sticky="w", pady=(0, 6))

        for i, (clave, etiqueta) in enumerate(_COLUMNAS):
            row = 5 + i * 2
            ttk.Label(self, text=etiqueta).grid(row=row, column=0, sticky="w", pady=(6, 0))
            ttk.Entry(self, textvariable=self._vars[clave], width=50).grid(
                row=row + 1, column=0, sticky="ew", pady=(2, 0))

        ttk.Separator(self, orient="horizontal").grid(
            row=5 + len(_COLUMNAS) * 2, column=0, sticky="ew", pady=(14, 8))

        # ── Columnas automáticas ──────────────────────────────────────────
        r = 5 + len(_COLUMNAS) * 2 + 1
        tk.Label(self, text="Columnas de seguimiento (se crean automáticamente):",
                 bg=C["bg_panel"], fg=C["acento"],
                 font=("Segoe UI", 9, "bold")).grid(row=r, column=0, sticky="w")

        info = (
            f"  • {COL_DOC_GENERADO} — \"Sí - DD/MM/YYYY HH:MM\" al generar el PDF\n"
            f"  • {COL_LINK_DRIVE}   — URL directa al archivo en Google Drive\n"
            f"  • {COL_CORREO_ESTADO} — \"Enviado / Fallido - DD/MM/YYYY HH:MM\"\n\n"
            "  Las filas con \"Enviado\" no se vuelven a procesar (deduplicación)."
        )
        tk.Label(
            self, text=info,
            bg=C["bg_panel"], fg=C["texto_dim"],
            font=("Segoe UI", 8), justify="left", anchor="w",
        ).grid(row=r + 1, column=0, sticky="w", pady=(4, 0))

    def recoger(self) -> dict:
        return {
            "spreadsheet_id": self._vars["spreadsheet_id"].get().strip(),
            "columnas": {clave: self._vars[clave].get().strip() for clave, _ in _COLUMNAS},
        }
