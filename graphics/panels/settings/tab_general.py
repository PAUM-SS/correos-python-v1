"""
graphics/panels/settings/tab_general.py
Pestaña ⚙ General:
  - Carpeta de Google Drive para almacenamiento permanente de PDFs
  - Formato del nombre de archivo: {campo} ConstSesion{sufijo}.pdf
  - Tamaño de lote y pausa entre correos
  - Rutas locales (plantilla PNG, carpeta de respaldo)
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog

from config import COLOR, COLUMN_CONFIG

class TabGeneral(tk.Frame):

    def __init__(self, padre, vars_: dict):
        super().__init__(padre, bg=COLOR["bg_panel"], padx=16, pady=14)
        self._vars = vars_
        self._construir()

    def _construir(self):
        C = COLOR
        self.columnconfigure(0, weight=1)
        row = 0

        # ── Google Drive — carpeta de almacenamiento ───────────────────────
        tk.Label(self, text="Carpeta de Google Drive para PDFs:",
                 bg=C["bg_panel"], fg=C["acento"],
                 font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, sticky="w"); row += 1

        ttk.Entry(self, textvariable=self._vars["drive_folder_id"], width=50).grid(
            row=row, column=0, sticky="ew", pady=(4, 0)); row += 1

        ttk.Label(
            self,
            text=(
                "ID de la carpeta en Drive (en la URL tras /folders/).\n"
                "Comparte la carpeta con el email del bot (rol Editor)."
            ),
            style="Sub.TLabel",
        ).grid(row=row, column=0, sticky="w", pady=(2, 0)); row += 1

        ttk.Separator(self, orient="horizontal").grid(
            row=row, column=0, sticky="ew", pady=(12, 8)); row += 1

        # ── Formato del nombre de archivo ─────────────────────────────────
        tk.Label(self, text="Formato del nombre de archivo:",
                 bg=C["bg_panel"], fg=C["acento"],
                 font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, sticky="w"); row += 1

        # Vista previa del nombre resultante
        self._lbl_preview = tk.Label(
            self, text="", bg=C["bg_input"], fg=C["listo"],
            font=("Consolas", 9), padx=8, pady=4, anchor="w",
        )
        self._lbl_preview.grid(row=row, column=0, sticky="ew", pady=(4, 0)); row += 1

        frame_nombre = tk.Frame(self, bg=C["bg_panel"])
        frame_nombre.grid(row=row, column=0, sticky="ew", pady=(6, 0)); row += 1

        ttk.Label(frame_nombre, text="Nombre de columna:").pack(side="left")
        ttk.Entry(frame_nombre, textvariable=self._vars["filename_campo"], width=18).pack(
            side="left", padx=(6, 0))
        self._vars["filename_campo"].trace_add("write", lambda *_: self._actualizar_preview())

        ttk.Label(frame_nombre, text="  ConstSesion").pack(side="left", padx=(12, 0))
        ttk.Entry(frame_nombre, textvariable=self._vars["filename_sufijo"], width=14).pack(side="left")
        ttk.Label(frame_nombre, text=".pdf").pack(side="left")

        self._vars["filename_sufijo"].trace_add("write", lambda *_: self._actualizar_preview())
        self._actualizar_preview()

        ttk.Separator(self, orient="horizontal").grid(
            row=row, column=0, sticky="ew", pady=(12, 8)); row += 1

        # ── Control de envío ──────────────────────────────────────────────
        tk.Label(self, text="Control de envío:",
                 bg=C["bg_panel"], fg=C["acento"],
                 font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, sticky="w"); row += 1

        frame_ctrl = tk.Frame(self, bg=C["bg_panel"])
        frame_ctrl.grid(row=row, column=0, sticky="w", pady=(6, 0)); row += 1

        ttk.Label(frame_ctrl, text="Máximo por lote:").pack(side="left")
        ttk.Spinbox(frame_ctrl, textvariable=self._vars["batch_size"],
                    from_=1, to=500, width=7).pack(side="left", padx=(6, 20))
        ttk.Label(frame_ctrl, text="Pausa entre correos (seg):").pack(side="left")
        ttk.Spinbox(frame_ctrl, textvariable=self._vars["email_delay"],
                    from_=0.5, to=10.0, increment=0.5, format="%.1f", width=7).pack(side="left", padx=(6, 0))

        ttk.Separator(self, orient="horizontal").grid(
            row=row, column=0, sticky="ew", pady=(12, 8)); row += 1

        # ── Rutas locales ─────────────────────────────────────────────────
        tk.Label(self, text="Rutas locales:",
                 bg=C["bg_panel"], fg=C["acento"],
                 font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, sticky="w"); row += 1

        ttk.Label(self, text="Plantilla PNG:").grid(row=row, column=0, sticky="w", pady=(6, 0)); row += 1
        f_tmpl = tk.Frame(self, bg=C["bg_panel"])
        f_tmpl.grid(row=row, column=0, sticky="ew"); row += 1
        ttk.Entry(f_tmpl, textvariable=self._vars["template_file"], width=44).pack(side="left", fill="x", expand=True)
        ttk.Button(f_tmpl, text="…", width=3,
                   command=lambda: self._vars["template_file"].set(
                       filedialog.askopenfilename(
                           title="Seleccionar plantilla",
                           filetypes=[("PNG", "*.png"), ("Todos", "*.*")],
                       ) or self._vars["template_file"].get()
                   )).pack(side="left", padx=(4, 0))

        ttk.Label(self, text="Carpeta de respaldo local:").grid(row=row, column=0, sticky="w", pady=(8, 0)); row += 1
        f_out = tk.Frame(self, bg=C["bg_panel"])
        f_out.grid(row=row, column=0, sticky="ew"); row += 1
        ttk.Entry(f_out, textvariable=self._vars["output_folder"], width=44).pack(side="left", fill="x", expand=True)
        ttk.Button(f_out, text="…", width=3,
                   command=lambda: self._vars["output_folder"].set(
                       filedialog.askdirectory(title="Seleccionar carpeta") or self._vars["output_folder"].get()
                   )).pack(side="left", padx=(4, 0))

    def _actualizar_preview(self):
        campo  = self._vars["filename_campo"].get() or "folio"
        sufijo = self._vars["filename_sufijo"].get()
        self._lbl_preview.config(text=f"  [{campo}] ConstSesion{sufijo}.pdf")

    def recoger(self) -> dict:
        return {
            "drive_folder_id": self._vars["drive_folder_id"].get().strip(),
            "filename_campo":  self._vars["filename_campo"].get().strip(),
            "filename_sufijo": self._vars["filename_sufijo"].get().strip(),
            "batch_size":      self._vars["batch_size"].get(),
            "email_delay":     self._vars["email_delay"].get(),
            "template_file":   self._vars["template_file"].get().strip(),
            "output_folder":   self._vars["output_folder"].get().strip(),
        }