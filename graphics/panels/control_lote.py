"""
graphics/panels/control_lote.py
Panel de control de envío: estadísticas, barra de progreso y botones de acción.
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk

from config import COLOR, BATCH_SIZE, OUTPUT_FOLDER
from graphics.panels._base import PanelBase


class PanelControlLote(PanelBase):
    """
    Panel con:
    - Chips de estadísticas (listos / enviados / fallidos).
    - Barra de progreso del lote actual.
    - Botones: Enviar lote, Detener, Abrir carpeta de salida.

    Expone:
        btn_enviar:          para habilitarlo/deshabilitarlo desde el orquestador.
        btn_detener:         ídem.
        lbl_stat_listos:     etiqueta del número de registros listos.
        lbl_stat_enviados:   etiqueta del número enviados.
        lbl_stat_fallidos:   etiqueta del número fallidos.
        lbl_progreso_txt:    texto "X / Y correos enviados".
    """

    def __init__(self, padre, app):
        super().__init__(padre, app, titulo="🚀  Control de Envío")
        self._construir()

    # ── Construcción ──────────────────────────────────────────────────────

    def _construir(self) -> None:
        C = COLOR
        contenedor = self.contenedor

        # ── Chips de estadísticas ─────────────────────────────────────────
        fila_stats = tk.Frame(contenedor, bg=C["bg_panel"])
        fila_stats.pack(fill="x", pady=(6, 8))

        self.lbl_stat_listos   = self._chip(fila_stats, "Listos",   "0", C["listo"])
        self.lbl_stat_enviados = self._chip(fila_stats, "Enviados", "0", C["enviado"])
        self.lbl_stat_fallidos = self._chip(fila_stats, "Fallidos", "0", C["fallido"])

        # ── Progreso ──────────────────────────────────────────────────────
        ttk.Label(contenedor, text="Progreso del lote actual:").pack(anchor="w")
        ttk.Progressbar(
            contenedor,
            variable=self.app.var_progreso,
            maximum=100,
            mode="determinate",
        ).pack(fill="x", pady=(2, 8))

        self.lbl_progreso_txt = ttk.Label(contenedor, text="0 / 0  correos enviados")
        self.lbl_progreso_txt.pack(anchor="w", pady=(0, 6))

        # ── Botones de control ────────────────────────────────────────────
        self.btn_enviar = ttk.Button(
            contenedor,
            text=f"▶  Enviar Siguiente Lote ({BATCH_SIZE})",
            style="Success.TButton",
            command=self.app.iniciar_envio_lote,
            state="disabled",
        )
        self.btn_enviar.pack(fill="x", pady=(0, 4))

        self.btn_detener = ttk.Button(
            contenedor,
            text="⛔  Detener Envío",
            style="Danger.TButton",
            command=self.app.detener_envio,
            state="disabled",
        )
        self.btn_detener.pack(fill="x")

        ttk.Separator(contenedor, orient="horizontal").pack(fill="x", pady=8)

        ttk.Button(
            contenedor,
            text="🗂  Abrir Carpeta de Salida",
            style="Primary.TButton",
            command=self._abrir_carpeta_salida,
        ).pack(fill="x")

    # ── Helpers visuales ──────────────────────────────────────────────────

    def _chip(self, padre: tk.Frame, etiqueta: str, valor: str, color: str) -> tk.Label:
        """Mini widget de estadística: número grande + etiqueta pequeña."""
        C = COLOR
        frame = tk.Frame(padre, bg=C["bg_input"], padx=8, pady=4)
        frame.pack(side="left", expand=True, fill="x", padx=2)

        lbl_num = tk.Label(frame, text=valor, bg=C["bg_input"], fg=color,
                           font=("Segoe UI", 14, "bold"))
        lbl_num.pack()

        tk.Label(frame, text=etiqueta, bg=C["bg_input"], fg=C["texto_dim"],
                 font=("Segoe UI", 7)).pack()

        return lbl_num   # retornamos la etiqueta del número para actualizarla

    # ── Acciones ──────────────────────────────────────────────────────────

    def _abrir_carpeta_salida(self) -> None:
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(OUTPUT_FOLDER)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", OUTPUT_FOLDER])
        else:
            subprocess.Popen(["xdg-open", OUTPUT_FOLDER])

    # ── Actualización desde el orquestador ────────────────────────────────

    def actualizar_estadisticas(self, listos: int, enviados: int, fallidos: int) -> None:
        self.lbl_stat_listos.config(text=str(listos))
        self.lbl_stat_enviados.config(text=str(enviados))
        self.lbl_stat_fallidos.config(text=str(fallidos))

    def actualizar_progreso(self, porcentaje: float, enviados: int, total: int) -> None:
        self.app.var_progreso.set(porcentaje)
        self.lbl_progreso_txt.config(text=f"{enviados} / {total}  correos enviados")

    def set_enviando(self, activo: bool) -> None:
        """Habilita / deshabilita los botones según si hay un envío en curso."""
        self.btn_enviar.config( state="disabled" if activo else "normal")
        self.btn_detener.config(state="normal"   if activo else "disabled")

    def habilitar_boton_enviar(self, habilitar: bool) -> None:
        self.btn_enviar.config(state="normal" if habilitar else "disabled")
