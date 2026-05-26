"""
graphics/panels/tabla.py
Panel con el Treeview que muestra todos los registros cargados desde Sheets,
coloreados por su estado (listo / enviando / enviado / fallido).
"""

import tkinter as tk
from tkinter import ttk

from config import COLOR, COLUMN_CONFIG


# Definición de columnas: (id_interno, encabezado_visible, ancho_px, stretch)
_COLUMNAS = [
    ("#",       "#",        40,  False),
    ("Nombre",  "Nombre",   170, True),
    ("Empresa", "Empresa",  140, True),
    ("Email",   "Email",    180, True),
    ("Folio",   "Folio",    80,  False),
    ("Estado",  "Estado",   110, False),
]


class PanelTabla(tk.Frame):
    """
    Frame con Treeview + scrollbars para visualizar los registros.

    Expone:
        tabla (ttk.Treeview): para que el orquestador inserte/actualice filas.
    """

    def __init__(self, padre, app):
        C = COLOR
        super().__init__(padre, bg=C["bg_oscuro"])
        self.pack(fill="both", expand=True, pady=(0, 6))

        self.app = app
        self._construir()

    # ── Construcción ──────────────────────────────────────────────────────

    def _construir(self) -> None:
        C = COLOR

        tk.Label(
            self,
            text="📊  Registros con Folio Asignado",
            bg=C["bg_oscuro"],
            fg=C["texto"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        # Frame contenedor para tabla + scrollbars (grid layout interno)
        frame = tk.Frame(self, bg=C["borde"])
        frame.pack(fill="both", expand=True)

        ids_col = [c[0] for c in _COLUMNAS]
        self.tabla = ttk.Treeview(frame, columns=ids_col, show="headings", selectmode="browse")

        for col_id, encabezado, ancho, stretch in _COLUMNAS:
            self.tabla.heading(col_id, text=encabezado)
            self.tabla.column(col_id, width=ancho, anchor="w", stretch=stretch)

        # Tags de color por estado
        self.tabla.tag_configure("listo",    background="#1A3A2A", foreground=C["listo"])
        self.tabla.tag_configure("enviado",  background="#1A2A3A", foreground=C["enviado"])
        self.tabla.tag_configure("fallido",  background="#3A1A1A", foreground=C["fallido"])
        self.tabla.tag_configure("enviando", background="#2A2A1A", foreground=C["advertencia"])

        scroll_y = ttk.Scrollbar(frame, orient="vertical",   command=self.tabla.yview)
        scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tabla.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    # ── API de actualización ──────────────────────────────────────────────

    def poblar(self, registros: list[dict]) -> tuple[int, int, int]:
        """
        Limpia la tabla y la repuebla con los registros proporcionados.

        Retorna:
            Tupla (listos, enviados, fallidos) para actualizar las estadísticas.
        """
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        listos = enviados = fallidos = 0

        for i, fila in enumerate(registros):
            estado_raw = str(fila.get(COLUMN_CONFIG["estado"], "")).strip()

            if not estado_raw:
                estado_txt = "Listo para enviar"
                tag        = "listo"
                fila["_estado_local"] = "listo"
                listos += 1
            elif estado_raw.lower() == "enviado":
                estado_txt = "Enviado"
                tag        = "enviado"
                fila["_estado_local"] = "enviado"
                enviados += 1
            elif estado_raw.lower() == "fallido":
                estado_txt = "Fallido"
                tag        = "fallido"
                fila["_estado_local"] = "fallido"
                fallidos += 1
            else:
                estado_txt = estado_raw
                tag        = "listo"
                fila["_estado_local"] = "listo"
                listos += 1

            self.tabla.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    i + 1,
                    fila.get(COLUMN_CONFIG["nombre"],  "—"),
                    fila.get(COLUMN_CONFIG["empresa"], "—"),
                    fila.get(COLUMN_CONFIG["email"],   "—"),
                    fila.get(COLUMN_CONFIG["folio"],   "—"),
                    estado_txt,
                ),
                tags=(tag,),
            )

        return listos, enviados, fallidos

    def actualizar_fila(self, idx: int, estado_txt: str, tag: str) -> None:
        """Actualiza el texto y color de una fila específica por su índice."""
        try:
            iid  = str(idx)
            vals = list(self.tabla.item(iid, "values"))
            vals[5] = estado_txt
            self.tabla.item(iid, values=vals, tags=(tag,))
        except Exception:
            pass
