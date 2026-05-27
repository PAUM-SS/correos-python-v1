"""
graphics/panels/settings/tab_credenciales.py
Pestaña 🔐 Credenciales:
  - Email remitente + contraseña de aplicación (SMTP Gmail)
  - Subir credentials.json OAuth2
  - Botón de autorización con Google (abre navegador)
  - Estado de autorización en tiempo real
  - Revocar token / re-autorizar
  - Pasos de configuración OAuth2
"""

import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import COLOR, CREDENTIALS_FILE
from auth.oauth import (
    autorizar_en_hilo,
    revocar_token,
    obtener_info_estado,
    credenciales_json_validas,
    TOKEN_FILE,
)


class TabCredenciales(tk.Frame):

    def __init__(self, padre, vars_: dict):
        super().__init__(padre, bg=COLOR["bg_panel"], padx=16, pady=14)
        self._vars = vars_
        self._construir()

    def _construir(self):
        C = COLOR
        self.columnconfigure(0, weight=1)

        # ── OAuth2 ────────────────────────────────────────────────────────
        tk.Label(self, text="Autorización Google (OAuth2):",
                 bg=C["bg_panel"], fg=C["acento"],
                 font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w")

        # Estado actual
        self._lbl_estado = tk.Label(
            self, text=self._texto_estado(),
            bg=C["bg_input"], fg=C["texto"],
            font=("Segoe UI", 9), padx=10, pady=5, anchor="w",
        )
        self._lbl_estado.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        # Botones de acción OAuth2
        frame_btns = tk.Frame(self, bg=C["bg_panel"])
        frame_btns.grid(row=2, column=0, sticky="w", pady=(8, 0))

        ttk.Button(frame_btns, text="📂  Subir credentials.json",
                   style="Primary.TButton",
                   command=self._subir_credentials).pack(side="left")

        self._btn_autorizar = ttk.Button(
            frame_btns, text="🔑  Autorizar con Google",
            style="Success.TButton",
            command=self._autorizar)
        self._btn_autorizar.pack(side="left", padx=(8, 0))

        ttk.Button(frame_btns, text="⟳ Re-autorizar",
                   style="Danger.TButton",
                   command=self._revocar_y_autorizar).pack(side="left", padx=(8, 0))

        ttk.Separator(self, orient="horizontal").grid(
            row=3, column=0, sticky="ew", pady=(14, 8))

        # ── Pasos de configuración OAuth2 ─────────────────────────────────
        tk.Label(self, text="Cómo configurar OAuth2:",
                 bg=C["bg_panel"], fg=C["acento"],
                 font=("Segoe UI", 9, "bold")).grid(
            row=4, column=0, sticky="w")

        pasos = (
            "1. Google Cloud Console → APIs y Servicios → Habilitar:\n"
            "     • Google Sheets API\n"
            "     • Google Drive API\n\n"
            "2. Credenciales → Crear credenciales → ID de cliente OAuth 2.0\n"
            "     Tipo: Aplicación de escritorio\n\n"
            "3. Pantalla de consentimiento OAuth → Agregar tu correo como\n"
            "   'Usuario de prueba' (si la app está en modo de prueba).\n\n"
            "4. Descargar el JSON → Subir con el botón 'Subir credentials.json'.\n\n"
            "5. Presionar 'Autorizar con Google' → se abre el navegador →\n"
            "   acepta los permisos → se genera token.json automáticamente.\n\n"
            "   La autorización se renueva sola. Solo necesitas repetirla\n"
            "   si revocas el acceso desde tu cuenta de Google."
        )
        tk.Label(
            self, text=pasos,
            bg=C["bg_panel"], fg=C["texto_dim"],
            font=("Segoe UI", 8), justify="left", anchor="w",
        ).grid(row=5, column=0, sticky="w", pady=(6, 0))

    # ── Helpers ───────────────────────────────────────────────────────────

    def _texto_estado(self) -> str:
        info = obtener_info_estado()
        return f"  {info['estado_txt']}"

    def _actualizar_estado(self):
        self._lbl_estado.config(text=self._texto_estado())

    def _subir_credentials(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar credentials.json (OAuth2)",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
        )
        if not ruta:
            return
        try:
            import json
            with open(ruta, encoding="utf-8") as f:
                data = json.load(f)
            if "installed" not in data and "web" not in data:
                messagebox.showerror(
                    "Formato incorrecto",
                    "Este archivo no es un credentials.json de OAuth2.\n\n"
                    "Debe tener la clave 'installed' (aplicación de escritorio).\n"
                    "No uses el JSON de Cuenta de Servicio.",
                )
                return
            shutil.copy(ruta, CREDENTIALS_FILE)
            self._actualizar_estado()
            messagebox.showinfo("Listo", "credentials.json OAuth2 actualizado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

    def _autorizar(self):
        if not credenciales_json_validas():
            messagebox.showwarning(
                "Falta credentials.json",
                "Primero sube el credentials.json de OAuth2.",
            )
            return
        self._lbl_estado.config(text="  ⏳ Abriendo navegador para autorización…")
        self._btn_autorizar.config(state="disabled")

        def ok(creds):
            self.after(0, lambda: self._lbl_estado.config(
                text="  ✔ Autorizado correctamente"))
            self.after(0, lambda: self._btn_autorizar.config(state="normal"))
            messagebox.showinfo("Autorizado", "¡Autorización completada! token.json guardado.")

        def err(msg):
            self.after(0, lambda: self._lbl_estado.config(
                text=f"  ❌ Error: {msg[:60]}"))
            self.after(0, lambda: self._btn_autorizar.config(state="normal"))
            messagebox.showerror("Error de autorización", msg)

        autorizar_en_hilo(ok, err)

    def _revocar_y_autorizar(self):
        if not messagebox.askyesno(
            "Re-autorizar",
            "Se eliminará el token guardado y se abrirá el navegador para autorizar de nuevo.\n"
            "¿Continuar?",
        ):
            return
        revocar_token()
        self._actualizar_estado()
        self._autorizar()

    def recoger(self) -> dict:
        return {}   # OAuth2 no requiere credenciales SMTP