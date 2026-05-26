"""
graphics/panels/settings_window.py
Ventana de configuración con pestañas (ttk.Notebook).
Se abre como Toplevel modal desde el botón ⚙ de la barra principal.

Pestañas:
  🔐 Credenciales  — email remitente + contraseña de aplicación
  ☁ Sheets         — Spreadsheet ID + nombres de columnas
  📋 Sesión        — ponencia, ponente, fecha (fijos para el lote)
  ⚙ General        — rutas, tamaño de lote, demora entre correos
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import COLOR
from config_manager import cargar_settings, guardar_settings, aplicar_settings, DEFAULTS
import copy


class VentanaConfiguracion(tk.Toplevel):
    """
    Ventana modal de configuración.
    Al guardar, escribe settings.json y aplica los valores en caliente.
    """

    def __init__(self, padre, app):
        super().__init__(padre)
        self.app      = app
        self.title("⚙  Configuración")
        self.geometry("600x560")
        self.resizable(False, False)
        self.configure(bg=COLOR["bg_oscuro"])
        self.focus_set()
        self.wait_visibility()   # esperar a que sea visible antes de grab
        self.grab_set()          # modal: bloquea la ventana principal

        # Cargar settings actuales
        self._settings = cargar_settings()

        # Variables Tkinter organizadas por sección
        self._vars: dict[str, dict[str, tk.Variable]] = {}

        self._construir()
        self._poblar_desde_settings()

        # Centrar sobre la ventana padre
        self.update_idletasks()
        x = padre.winfo_x() + (padre.winfo_width()  - self.winfo_width())  // 2
        y = padre.winfo_y() + (padre.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    # ══════════════════════════════════════════════════════════════════════
    #  CONSTRUCCIÓN
    # ══════════════════════════════════════════════════════════════════════

    def _construir(self) -> None:
        C = COLOR

        # Notebook (pestañas)
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=14, pady=(14, 0))

        self._tab_credenciales(nb)
        self._tab_sheets(nb)
        self._tab_sesion(nb)
        self._tab_general(nb)

        # Barra de botones inferior
        barra = tk.Frame(self, bg=C["bg_oscuro"], pady=10)
        barra.pack(fill="x", padx=14)

        ttk.Button(barra, text="💾  Guardar y Aplicar",
                   style="Success.TButton", command=self._guardar).pack(side="left")
        ttk.Button(barra, text="Restaurar defaults",
                   style="Primary.TButton", command=self._restaurar).pack(side="left", padx=(8, 0))
        ttk.Button(barra, text="Cancelar",
                   style="Danger.TButton", command=self.destroy).pack(side="right")

    # ── Pestaña: Credenciales ─────────────────────────────────────────────

    def _tab_credenciales(self, nb: ttk.Notebook) -> None:
        frame = self._nuevo_tab(nb, "🔐  Credenciales")
        self._vars["credenciales"] = {}

        self._campo(frame, "credenciales", "remitente",
                    "Correo remitente (Gmail):", row=0)

        # Contraseña con toggle
        ttk.Label(frame, text="Contraseña de aplicación:").grid(
            row=2, column=0, sticky="w", pady=(10, 2))

        var_pass = tk.StringVar()
        self._vars["credenciales"]["contrasena"] = var_pass
        entry_pass = ttk.Entry(frame, textvariable=var_pass, show="●", width=42)
        entry_pass.grid(row=3, column=0, columnspan=2, sticky="ew")

        var_mostrar = tk.BooleanVar(value=False)
        tk.Checkbutton(
            frame, text="Mostrar contraseña",
            variable=var_mostrar,
            bg=COLOR["bg_panel"], fg=COLOR["texto_dim"],
            selectcolor=COLOR["bg_input"], activebackground=COLOR["bg_panel"],
            font=("Segoe UI", 8),
            command=lambda: entry_pass.config(show="" if var_mostrar.get() else "●"),
        ).grid(row=4, column=0, sticky="w", pady=(2, 0))

        # Nota informativa
        nota = tk.Label(
            frame,
            text=(
                "⚠  Usa una Contraseña de Aplicación de Google (16 caracteres),\n"
                "    no tu contraseña habitual. Genera una en:\n"
                "    myaccount.google.com → Seguridad → Contraseñas de aplicaciones\n\n"
                "⚠  Las credenciales se guardan en settings.json (texto plano).\n"
                "    No subas ese archivo a repositorios públicos."
            ),
            bg=COLOR["bg_panel"], fg=COLOR["texto_dim"],
            font=("Segoe UI", 8), justify="left",
        )
        nota.grid(row=5, column=0, columnspan=2, sticky="w", pady=(14, 0))

    # ── Pestaña: Google Sheets ────────────────────────────────────────────

    def _tab_sheets(self, nb: ttk.Notebook) -> None:
        frame = self._nuevo_tab(nb, "☁  Google Sheets")
        self._vars["sheets"]  = {}
        self._vars["columnas"] = {}

        # Spreadsheet ID
        self._campo(frame, "sheets", "spreadsheet_id",
                    "Spreadsheet ID:", row=0)
        ttk.Label(frame, text="(parte de la URL entre /d/ y /edit)",
                  style="Sub.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 10))

        ttk.Separator(frame, orient="horizontal").grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        # Nombres de columnas
        tk.Label(frame, text="Nombres exactos de columnas en la hoja:",
                 bg=COLOR["bg_panel"], fg=COLOR["acento"],
                 font=("Segoe UI", 9, "bold")).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(0, 6))

        columnas_labels = [
            ("nombre",   "Nombre(s):"),
            ("apellido", "Apellido(s):"),
            ("email",    "Correo electrónico:"),
            ("folio",    "Número de Folio:"),
            ("fecha",    "Timestamp / Fecha:"),
            ("estado",   "Estado (control):"),
        ]
        for i, (clave, etiqueta) in enumerate(columnas_labels):
            self._campo(frame, "columnas", clave, etiqueta, row=5 + i * 2)

    # ── Pestaña: Sesión ───────────────────────────────────────────────────

    def _tab_sesion(self, nb: ttk.Notebook) -> None:
        frame = self._nuevo_tab(nb, "📋  Sesión")
        self._vars["sesion"] = {}

        tk.Label(
            frame,
            text="Datos fijos para todo el lote actual.\nSe insertan en los campos <<Ponencia>>, <<Ponente>>, <<Fecha>>.",
            bg=COLOR["bg_panel"], fg=COLOR["texto_dim"],
            font=("Segoe UI", 8), justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self._campo(frame, "sesion", "ponencia", "Ponencia / Tema:", row=2)
        self._campo(frame, "sesion", "ponente",  "Ponente:",         row=4)
        self._campo(frame, "sesion", "fecha",    "Fecha del evento:", row=6)

    # ── Pestaña: General ──────────────────────────────────────────────────

    def _tab_general(self, nb: ttk.Notebook) -> None:
        frame = self._nuevo_tab(nb, "⚙  General")
        self._vars["general"] = {}

        # Plantilla
        ttk.Label(frame, text="Archivo de plantilla (.png):").grid(
            row=0, column=0, sticky="w", pady=(0, 2))
        var_tmpl = tk.StringVar()
        self._vars["general"]["template_file"] = var_tmpl

        f_tmpl = tk.Frame(frame, bg=COLOR["bg_panel"])
        f_tmpl.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Entry(f_tmpl, textvariable=var_tmpl, width=34).pack(side="left", fill="x", expand=True)
        ttk.Button(f_tmpl, text="…", width=3,
                   command=lambda: var_tmpl.set(
                       filedialog.askopenfilename(
                           title="Seleccionar plantilla",
                           filetypes=[("PNG", "*.png"), ("Todos", "*.*")],
                           initialfile=var_tmpl.get(),
                       ) or var_tmpl.get()
                   )).pack(side="left", padx=(4, 0))

        # Carpeta de salida
        ttk.Label(frame, text="Carpeta de salida (PDFs):").grid(
            row=2, column=0, sticky="w", pady=(10, 2))
        var_out = tk.StringVar()
        self._vars["general"]["output_folder"] = var_out

        f_out = tk.Frame(frame, bg=COLOR["bg_panel"])
        f_out.grid(row=3, column=0, columnspan=2, sticky="ew")
        ttk.Entry(f_out, textvariable=var_out, width=34).pack(side="left", fill="x", expand=True)
        ttk.Button(f_out, text="…", width=3,
                   command=lambda: var_out.set(
                       filedialog.askdirectory(title="Seleccionar carpeta de salida") or var_out.get()
                   )).pack(side="left", padx=(4, 0))

        ttk.Separator(frame, orient="horizontal").grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(14, 8))

        # Batch size
        ttk.Label(frame, text="Máximo de correos por lote:").grid(
            row=5, column=0, sticky="w")
        var_batch = tk.IntVar()
        self._vars["general"]["batch_size"] = var_batch
        ttk.Spinbox(frame, textvariable=var_batch, from_=1, to=500,
                    width=8).grid(row=5, column=1, sticky="w", padx=(8, 0))

        # Email delay
        ttk.Label(frame, text="Pausa entre correos (segundos):").grid(
            row=6, column=0, sticky="w", pady=(8, 0))
        var_delay = tk.DoubleVar()
        self._vars["general"]["email_delay"] = var_delay
        ttk.Spinbox(frame, textvariable=var_delay, from_=0.5, to=10.0,
                    increment=0.5, format="%.1f", width=8).grid(
            row=6, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

    # ══════════════════════════════════════════════════════════════════════
    #  HELPERS DE CONSTRUCCIÓN
    # ══════════════════════════════════════════════════════════════════════

    def _nuevo_tab(self, nb: ttk.Notebook, titulo: str) -> tk.Frame:
        """Crea una pestaña con frame interior con padding uniforme."""
        outer = tk.Frame(nb, bg=COLOR["bg_panel"])
        nb.add(outer, text=f"  {titulo}  ")
        frame = tk.Frame(outer, bg=COLOR["bg_panel"], padx=16, pady=14)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        return frame

    def _campo(self, frame: tk.Frame, seccion: str, clave: str,
               etiqueta: str, row: int) -> None:
        """Crea un par Label + Entry y registra la variable en self._vars."""
        C = COLOR
        ttk.Label(frame, text=etiqueta).grid(
            row=row, column=0, sticky="w", pady=(8 if row > 0 else 0, 2))
        var = tk.StringVar()
        self._vars[seccion][clave] = var
        ttk.Entry(frame, textvariable=var, width=42).grid(
            row=row + 1, column=0, columnspan=2, sticky="ew")

    # ══════════════════════════════════════════════════════════════════════
    #  LÓGICA DE DATOS
    # ══════════════════════════════════════════════════════════════════════

    def _poblar_desde_settings(self) -> None:
        """Rellena los campos de la UI con los valores de self._settings."""
        for seccion, campos in self._vars.items():
            datos_seccion = self._settings.get(seccion, {})
            for clave, var in campos.items():
                valor = datos_seccion.get(clave, "")
                if isinstance(var, tk.IntVar):
                    try:
                        var.set(int(valor))
                    except (ValueError, TypeError):
                        var.set(0)
                elif isinstance(var, tk.DoubleVar):
                    try:
                        var.set(float(valor))
                    except (ValueError, TypeError):
                        var.set(0.0)
                else:
                    var.set(str(valor))

    def _recoger_settings(self) -> dict:
        """Lee los valores actuales de la UI y los convierte a dict."""
        resultado = {}
        for seccion, campos in self._vars.items():
            resultado[seccion] = {}
            for clave, var in campos.items():
                resultado[seccion][clave] = var.get()
        return resultado

    def _guardar(self) -> None:
        """Guarda en disco, aplica en caliente y actualiza variables de la app."""
        nuevo = self._recoger_settings()
        guardar_settings(nuevo)
        aplicar_settings(nuevo)

        # Sincronizar variables Tkinter de la app principal
        creds = nuevo.get("credenciales", {})
        if creds.get("remitente"):
            self.app.var_remitente.set(creds["remitente"])
        if creds.get("contrasena"):
            self.app.var_contrasena.set(creds["contrasena"])

        sheets = nuevo.get("sheets", {})
        if sheets.get("spreadsheet_id"):
            self.app.var_sheet_id.set(sheets["spreadsheet_id"])

        self.app.log("✔ Configuración guardada y aplicada.", "ok")
        messagebox.showinfo("Guardado", "Configuración guardada correctamente.", parent=self)
        self.destroy()

    def _restaurar(self) -> None:
        """Restaura todos los campos a los valores por defecto."""
        if messagebox.askyesno(
            "Restaurar",
            "¿Restaurar todos los campos a los valores por defecto?\n"
            "Los cambios no guardados se perderán.",
            parent=self,
        ):
            self._settings = copy.deepcopy(DEFAULTS)
            self._poblar_desde_settings()
