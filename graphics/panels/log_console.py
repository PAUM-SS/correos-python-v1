"""
graphics/panels/log_console.py
Panel inferior de consola de actividad: área de texto con timestamps y colores
por nivel (info / ok / warn / err). Thread-safe mediante app.after().
"""

import datetime
import tkinter as tk
from tkinter import ttk

from config import COLOR


class PanelLog(tk.Frame):
    """
    Consola de log en tiempo real.
    Siempre se ubica en la parte inferior del panel derecho.

    Uso:
        panel_log.escribir("Mensaje", nivel="ok")
        panel_log.limpiar()
    """

    PREFIJOS = {
        "info": "ℹ ",
        "ok":   "✔ ",
        "warn": "⚠ ",
        "err":  "✘ ",
    }

    def __init__(self, padre, app):
        C = COLOR
        super().__init__(padre, bg=C["bg_oscuro"])
        self.pack(fill="x", side="bottom")

        self.app = app
        self._construir()

    # ── Construcción ──────────────────────────────────────────────────────

    def _construir(self) -> None:
        C = COLOR

        # Encabezado con botón de limpiar
        encabezado = tk.Frame(self, bg=C["bg_oscuro"])
        encabezado.pack(fill="x")

        tk.Label(
            encabezado,
            text="📋  Consola de Actividad",
            bg=C["bg_oscuro"],
            fg=C["texto"],
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", pady=(0, 4))

        tk.Button(
            encabezado,
            text="Limpiar",
            bg=C["bg_panel"],
            fg=C["texto_dim"],
            font=("Segoe UI", 8),
            bd=0,
            cursor="hand2",
            command=self.limpiar,
        ).pack(side="right")

        # Área de texto con altura fija
        frame_txt = tk.Frame(self, bg=C["borde"], height=160)
        frame_txt.pack(fill="x")
        frame_txt.pack_propagate(False)

        self._txt = tk.Text(
            frame_txt,
            bg=C["bg_input"],
            fg=C["texto"],
            font=("Consolas", 8),
            wrap="word",
            bd=0,
            padx=8,
            pady=6,
            state="disabled",
        )
        scroll = ttk.Scrollbar(frame_txt, command=self._txt.yview)
        self._txt.configure(yscrollcommand=scroll.set)

        self._txt.pack(side="left",  fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Tags de color por nivel
        self._txt.tag_configure("ok",   foreground=C["listo"])
        self._txt.tag_configure("err",  foreground=C["error"])
        self._txt.tag_configure("info", foreground=C["acento"])
        self._txt.tag_configure("warn", foreground=C["advertencia"])

    # ── API pública ───────────────────────────────────────────────────────

    def escribir(self, mensaje: str, nivel: str = "info") -> None:
        """
        Inserta una línea en la consola con timestamp.
        Seguro para llamar desde hilos secundarios (usa app.after()).
        """
        def _hacer():
            ts      = datetime.datetime.now().strftime("%H:%M:%S")
            prefijo = self.PREFIJOS.get(nivel, "  ")
            linea   = f"[{ts}] {prefijo}{mensaje}\n"

            self._txt.config(state="normal")
            self._txt.insert("end", linea, nivel)
            self._txt.see("end")
            self._txt.config(state="disabled")

        self.app.after(0, _hacer)

    def limpiar(self) -> None:
        """Borra todo el contenido de la consola."""
        self._txt.config(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.config(state="disabled")
