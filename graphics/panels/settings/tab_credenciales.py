"""
graphics/panels/settings/tab_credenciales.py
Pestaña 🔐 Credenciales:
  - Email remitente + contraseña de aplicación
  - Subir nuevo credentials.json
  - Info del bot (email de la cuenta de servicio + pasos de configuración)
"""

import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import COLOR, CREDENTIALS_FILE
from auth   import obtener_email_bot, credenciales_validas


class TabCredenciales(tk.Frame):

    def __init__(self, padre, vars_: dict):
        """
        vars_: dict compartido con main_window que contiene todas las StringVars.
        """
        super().__init__(padre, bg=COLOR["bg_panel"], padx=16, pady=14)
        self._vars = vars_
        self._construir()

    def _construir(self):
        C = COLOR
        self.columnconfigure(0, weight=1)

        # ── Email ────────────────────────────────────────────────────────
        ttk.Label(self, text="Correo remitente (Gmail):").grid(
            row=0, column=0, sticky="w")
        ttk.Entry(self, textvariable=self._vars["remitente"], width=50).grid(
            row=1, column=0, sticky="ew", pady=(2, 0))

        # ── Contraseña ───────────────────────────────────────────────────
        ttk.Label(self, text="Contraseña de aplicación (16 caracteres):").grid(
            row=2, column=0, sticky="w", pady=(10, 0))

        self._entry_pass = ttk.Entry(
            self, textvariable=self._vars["contrasena"], show="●", width=50)
        self._entry_pass.grid(row=3, column=0, sticky="ew", pady=(2, 0))

        var_show = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self, text="Mostrar contraseña",
            variable=var_show,
            bg=C["bg_panel"], fg=C["texto_dim"],
            selectcolor=C["bg_input"], activebackground=C["bg_panel"],
            font=("Segoe UI", 8),
            command=lambda: self._entry_pass.config(show="" if var_show.get() else "●"),
        ).grid(row=4, column=0, sticky="w", pady=(2, 0))

        ttk.Label(
            self,
            text="⚠ Genera la contraseña en: myaccount.google.com → Seguridad → Contraseñas de aplicaciones",
            style="Sub.TLabel",
        ).grid(row=5, column=0, sticky="w", pady=(4, 0))

        ttk.Separator(self, orient="horizontal").grid(
            row=6, column=0, sticky="ew", pady=(14, 8))

        # ── Credentials.json ─────────────────────────────────────────────
        tk.Label(self, text="Cuenta de Servicio de Google:",
                 bg=C["bg_panel"], fg=C["acento"],
                 font=("Segoe UI", 9, "bold")).grid(
            row=7, column=0, sticky="w")

        self._lbl_bot = tk.Label(
            self, text=self._email_bot(),
            bg=C["bg_input"], fg=C["texto"],
            font=("Consolas", 8), padx=8, pady=4, anchor="w",
        )
        self._lbl_bot.grid(row=8, column=0, sticky="ew", pady=(4, 0))

        ttk.Button(
            self, text="📂  Subir nuevo credentials.json",
            style="Primary.TButton",
            command=self._subir_credentials,
        ).grid(row=9, column=0, sticky="w", pady=(8, 0))

        ttk.Separator(self, orient="horizontal").grid(
            row=10, column=0, sticky="ew", pady=(14, 8))

        # ── Pasos de configuración ────────────────────────────────────────
        tk.Label(self, text="Cómo autorizar al bot:",
                 bg=C["bg_panel"], fg=C["acento"],
                 font=("Segoe UI", 9, "bold")).grid(
            row=11, column=0, sticky="w")

        pasos = (
            "1. Habilita 'Google Sheets API' y 'Google Drive API' en Google Cloud Console.\n"
            "2. Crea una Cuenta de Servicio → descarga el JSON → súbelo aquí.\n"
            "3. Abre tu Google Sheet → Compartir → pega el email del bot → rol Editor.\n"
            "4. Crea una carpeta en Drive → Compartir con el email del bot → Editor.\n"
            "   Copia el ID de la carpeta y pégalo en la pestaña ⚙ General."
        )
        tk.Label(
            self, text=pasos,
            bg=C["bg_panel"], fg=C["texto_dim"],
            font=("Segoe UI", 8), justify="left", anchor="w",
        ).grid(row=12, column=0, sticky="w", pady=(4, 0))

    def _email_bot(self) -> str:
        email = obtener_email_bot()
        ok    = credenciales_validas()
        return f"{'✔' if ok else '⚠'}  {email}"

    def _subir_credentials(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar credentials.json",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
        )
        if not ruta:
            return
        try:
            import json
            with open(ruta, encoding="utf-8") as f:
                data = json.load(f)
            assert data.get("type") == "service_account", "No es una Cuenta de Servicio"
            shutil.copy(ruta, CREDENTIALS_FILE)
            self._lbl_bot.config(text=self._email_bot())
            messagebox.showinfo("Listo", f"credentials.json actualizado.\nBot: {data['client_email']}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

    def recoger(self) -> dict:
        return {
            "remitente":  self._vars["remitente"].get().strip(),
            "contrasena": self._vars["contrasena"].get(),
        }
