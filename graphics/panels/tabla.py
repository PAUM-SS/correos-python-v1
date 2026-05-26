"""
graphics/panels/tabla.py
Treeview con registros cargados desde Sheets.
Columnas: # | Nombre | Apellido | Email | Folio | Estado
(se eliminó Empresa)
"""

import tkinter as tk
from tkinter import ttk

from config import COLOR, COLUMN_CONFIG

_COLUMNAS = [
    ("#",        "#",         40,  False),
    ("Nombre",   "Nombre",    150, True),
    ("Apellido", "Apellido",  140, True),
    ("Email",    "Email",     200, True),
    ("Folio",    "Folio",     100, False),
    ("Estado",   "Estado",    155, False),
]


class PanelTabla(tk.Frame):

    def __init__(self, padre, app):
        C = COLOR
        super().__init__(padre, bg=C["bg_oscuro"])
        self.pack(fill="both", expand=True, pady=(0, 6))
        self.app = app
        self._construir()

    def _construir(self):
        C = COLOR
        tk.Label(
            self, text="📊  Registros con Folio Asignado",
            bg=C["bg_oscuro"], fg=C["texto"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        frame = tk.Frame(self, bg=C["borde"])
        frame.pack(fill="both", expand=True)

        ids = [c[0] for c in _COLUMNAS]
        self.tabla = ttk.Treeview(frame, columns=ids, show="headings", selectmode="browse")
        for col_id, encabezado, ancho, stretch in _COLUMNAS:
            self.tabla.heading(col_id, text=encabezado)
            self.tabla.column(col_id, width=ancho, anchor="w", stretch=stretch)

        self.tabla.tag_configure("listo",    background="#1A3A2A", foreground=C["listo"])
        self.tabla.tag_configure("enviado",  background="#1A2A3A", foreground=C["enviado"])
        self.tabla.tag_configure("fallido",  background="#3A1A1A", foreground=C["fallido"])
        self.tabla.tag_configure("enviando", background="#2A2A1A", foreground=C["advertencia"])

        sy = ttk.Scrollbar(frame, orient="vertical",   command=self.tabla.yview)
        sx = ttk.Scrollbar(frame, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tabla.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    def poblar(self, registros: list[dict]) -> tuple[int, int, int]:
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        listos = enviados = fallidos = 0

        for i, fila in enumerate(registros):
            estado_local = fila.get("_estado_local", "listo")

            if estado_local == "enviado":
                estado_txt = "Enviado"; enviados += 1
            elif estado_local == "fallido":
                estado_txt = "Fallido"; fallidos += 1
            else:
                estado_txt = "Listo para enviar"; listos += 1
                fila["_estado_local"] = "listo"

            self.tabla.insert(
                "", "end", iid=str(i),
                values=(
                    i + 1,
                    fila.get(COLUMN_CONFIG.get("nombre",   "Nombres"),   "—"),
                    fila.get(COLUMN_CONFIG.get("apellido", "Apellidos"), "—"),
                    fila.get(COLUMN_CONFIG.get("email",    "Email"),     "—"),
                    fila.get(COLUMN_CONFIG.get("folio",    "Folio"),     "—"),
                    estado_txt,
                ),
                tags=(estado_local,),
            )

        return listos, enviados, fallidos

    def actualizar_fila(self, idx: int, estado_txt: str, tag: str):
        try:
            iid  = str(idx)
            vals = list(self.tabla.item(iid, "values"))
            vals[5] = estado_txt
            self.tabla.item(iid, values=vals, tags=(tag,))
        except Exception:
            pass
