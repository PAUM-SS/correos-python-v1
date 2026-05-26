"""
graphics/panels/sheets_panel.py
Panel de configuración de Google Sheets: campo de Spreadsheet ID y botón de carga.
"""

from tkinter import ttk

from graphics.panels._base import PanelBase


class PanelSheets(PanelBase):
    """
    Sección con el campo del Spreadsheet ID y el botón para cargar datos.

    Expone:
        lbl_registros: etiqueta actualizable con el total de registros cargados.
    """

    def __init__(self, padre, app):
        super().__init__(padre, app, titulo="☁  Google Sheets")
        self._construir()

    # ── Construcción ──────────────────────────────────────────────────────

    def _construir(self) -> None:
        contenedor = self.contenedor

        ttk.Label(contenedor, text="Spreadsheet ID:").pack(anchor="w", pady=(6, 1))
        ttk.Entry(contenedor, textvariable=self.app.var_sheet_id, width=34).pack(fill="x")

        ttk.Label(
            contenedor,
            text="(Parte de la URL entre /d/ y /edit)",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        ttk.Button(
            contenedor,
            text="☁  Cargar Datos desde la Nube",
            style="Primary.TButton",
            command=self.app.iniciar_carga_datos,   # delegado al orquestador
        ).pack(fill="x", pady=(10, 2))

        self.lbl_registros = ttk.Label(contenedor, text="Registros con folio: —")
        self.lbl_registros.pack(anchor="w", pady=(4, 0))

    # ── Actualización ─────────────────────────────────────────────────────

    def actualizar_contador(self, total: int) -> None:
        """Actualiza el texto del contador de registros."""
        self.lbl_registros.config(text=f"Registros con folio: {total}")
