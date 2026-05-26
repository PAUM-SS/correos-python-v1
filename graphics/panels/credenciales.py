"""
graphics/panels/credenciales.py
Panel de credenciales de correo: campo de remitente y contraseña de aplicación.
"""

import tkinter as tk
from tkinter import ttk

from config import COLOR
from graphics.panels._base import PanelBase


class PanelCredenciales(PanelBase):
    """
    Sección visual con los campos de autenticación SMTP.

    Expone:
        var_remitente  (tk.StringVar): email del remitente.
        var_contrasena (tk.StringVar): contraseña de aplicación.
    """

    def __init__(self, padre, app):
        super().__init__(padre, app, titulo="🔐  Credenciales de Envío")
        self._construir()

    # ── Construcción ──────────────────────────────────────────────────────

    def _construir(self) -> None:
        C = COLOR
        contenedor = self.contenedor   # frame interior de la tarjeta

        # ── Email remitente ───────────────────────────────────────────────
        ttk.Label(contenedor, text="Correo Remitente (Gmail):").pack(anchor="w", pady=(6, 1))
        ttk.Entry(contenedor, textvariable=self.app.var_remitente, width=34).pack(fill="x")

        # ── Contraseña ────────────────────────────────────────────────────
        ttk.Label(contenedor, text="Contraseña de Aplicación:").pack(anchor="w", pady=(6, 1))

        self._entry_pass = ttk.Entry(
            contenedor,
            textvariable=self.app.var_contrasena,
            show="●",
            width=34,
        )
        self._entry_pass.pack(fill="x")

        # Toggle mostrar / ocultar contraseña
        self._var_mostrar = tk.BooleanVar(value=False)
        tk.Checkbutton(
            contenedor,
            text="Mostrar contraseña",
            variable=self._var_mostrar,
            bg=C["bg_panel"],
            fg=C["texto_dim"],
            selectcolor=C["bg_input"],
            activebackground=C["bg_panel"],
            font=("Segoe UI", 8),
            command=self._toggle_pass,
        ).pack(anchor="w", pady=(2, 0))

        # Nota informativa
        ttk.Label(
            contenedor,
            text="⚠ Usa una Contraseña de Aplicación,\n   no tu contraseña habitual de Gmail.",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(4, 0))

    # ── Eventos ───────────────────────────────────────────────────────────

    def _toggle_pass(self) -> None:
        self._entry_pass.config(show="" if self._var_mostrar.get() else "●")
