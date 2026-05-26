"""
graphics/panels/settings/main_window.py
Ventana modal de configuración.
Ensambla las 5 pestañas y gestiona el ciclo cargar → editar → guardar.
"""

import copy
import tkinter as tk
from tkinter import ttk, messagebox

from config import COLOR
from config_manager import cargar_settings, guardar_settings, aplicar_settings, DEFAULTS

from graphics.panels.settings.tab_credenciales import TabCredenciales
from graphics.panels.settings.tab_sheets       import TabSheets
from graphics.panels.settings.tab_sesion       import TabSesion
from graphics.panels.settings.tab_email        import TabEmail
from graphics.panels.settings.tab_general      import TabGeneral


class VentanaConfiguracion(tk.Toplevel):
    """
    Ventana modal de configuración con 5 pestañas.
    Al guardar escribe settings.json y aplica los valores en caliente.
    """

    def __init__(self, padre, app):
        super().__init__(padre)
        self.app = app
        self.title("⚙  Configuración")
        self.geometry("660x620")
        self.resizable(True, True)
        self.minsize(600, 540)
        self.configure(bg=COLOR["bg_oscuro"])

        self._settings = cargar_settings()
        self._vars: dict[str, tk.Variable] = {}
        self._tabs: dict[str, object]       = {}

        self._crear_variables()
        self._construir()
        self._poblar()
        self._centrar(padre)

        self.focus_set()
        self.wait_visibility()
        self.grab_set()

    # ══════════════════════════════════════════════════════════════════════
    #  VARIABLES COMPARTIDAS
    # ══════════════════════════════════════════════════════════════════════

    def _crear_variables(self):
        s = tk.StringVar
        i = tk.IntVar
        d = tk.DoubleVar

        self._vars = {
            # Credenciales
            "remitente":       s(), "contrasena":     s(),
            # Sheets
            "spreadsheet_id":  s(),
            # Columnas
            "nombre": s(), "apellido": s(), "email": s(),
            "folio":  s(), "fecha":    s(),
            # Sesión
            "ponencia": s(), "ponente": s(), "fecha_sesion": s(),
            # Email
            "asunto": s(),
            # Drive / General
            "drive_folder_id": s(),
            "filename_campo":  s(), "filename_sufijo": s(),
            "batch_size":      i(), "email_delay":     d(),
            "template_file":   s(), "output_folder":   s(),
        }

    # ══════════════════════════════════════════════════════════════════════
    #  CONSTRUCCIÓN
    # ══════════════════════════════════════════════════════════════════════

    def _construir(self):
        C = COLOR

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=14, pady=(14, 0))

        def agregar(cls, titulo, *args, **kwargs):
            tab = cls(nb, *args, **kwargs)
            nb.add(tab, text=f"  {titulo}  ")
            return tab

        # Reusar _vars para sesión con clave renombrada
        vars_sesion = {
            "ponencia": self._vars["ponencia"],
            "ponente":  self._vars["ponente"],
            "fecha":    self._vars["fecha_sesion"],
        }

        self._tabs["creds"]   = agregar(TabCredenciales, "🔐 Credenciales",  self._vars)
        self._tabs["sheets"]  = agregar(TabSheets,       "☁ Sheets",         self._vars)
        self._tabs["sesion"]  = agregar(TabSesion,       "📋 Sesión",        vars_sesion)
        self._tabs["email"]   = agregar(TabEmail,        "📧 Correo",        self._vars)
        self._tabs["general"] = agregar(TabGeneral,      "⚙ General",        self._vars)

        # Barra inferior
        barra = tk.Frame(self, bg=COLOR["bg_oscuro"], pady=10)
        barra.pack(fill="x", padx=14)

        ttk.Button(barra, text="💾  Guardar y Aplicar",
                   style="Success.TButton", command=self._guardar).pack(side="left")
        ttk.Button(barra, text="Restaurar defaults",
                   style="Primary.TButton",
                   command=self._restaurar).pack(side="left", padx=(8, 0))
        ttk.Button(barra, text="Cancelar",
                   style="Danger.TButton", command=self.destroy).pack(side="right")

    # ══════════════════════════════════════════════════════════════════════
    #  POBLADO DESDE SETTINGS
    # ══════════════════════════════════════════════════════════════════════

    def _poblar(self):
        s = self._settings
        v = self._vars

        def sv(var_name, value):
            var = v.get(var_name)
            if var is None:
                return
            if isinstance(var, tk.IntVar):
                try: var.set(int(value))
                except: var.set(0)
            elif isinstance(var, tk.DoubleVar):
                try: var.set(float(value))
                except: var.set(0.0)
            else:
                var.set(str(value))

        creds   = s.get("credenciales",  {})
        sheets  = s.get("sheets",        {})
        cols    = s.get("columnas",      {})
        sesion  = s.get("sesion",        {})
        email   = s.get("email_cuerpo",  {})
        drive   = s.get("drive",         {})
        general = s.get("general",       {})

        sv("remitente",       creds.get("remitente", ""))
        sv("contrasena",      creds.get("contrasena", ""))
        sv("spreadsheet_id",  sheets.get("spreadsheet_id", ""))

        for col in ("nombre", "apellido", "email", "folio", "fecha"):
            sv(col, cols.get(col, ""))

        sv("ponencia",     sesion.get("ponencia", ""))
        sv("ponente",      sesion.get("ponente",  ""))
        sv("fecha_sesion", sesion.get("fecha",    ""))

        sv("asunto", email.get("asunto", ""))
        self._tabs["email"].poblar(
            email.get("asunto", ""),
            email.get("html",   ""),
        )

        sv("drive_folder_id", drive.get("folder_id", ""))
        sv("filename_campo",  general.get("filename_campo",  "folio"))
        sv("filename_sufijo", general.get("filename_sufijo", ""))
        sv("batch_size",      general.get("batch_size",  100))
        sv("email_delay",     general.get("email_delay", 1.5))
        sv("template_file",   general.get("template_file", "plantilla_constancia.png"))
        sv("output_folder",   general.get("output_folder", "constancias_generadas"))

    # ══════════════════════════════════════════════════════════════════════
    #  GUARDAR
    # ══════════════════════════════════════════════════════════════════════

    def _guardar(self):
        v  = self._vars
        ts = self._tabs

        sheets_data  = ts["sheets"].recoger()
        email_data   = ts["email"].recoger()
        general_data = ts["general"].recoger()

        nuevo = {
            "credenciales": ts["creds"].recoger(),
            "sheets":       {"spreadsheet_id": sheets_data["spreadsheet_id"]},
            "columnas":     sheets_data["columnas"],
            "sesion":       ts["sesion"].recoger(),
            "email_cuerpo": email_data,
            "drive":        {"folder_id": general_data.pop("drive_folder_id")},
            "general":      general_data,
        }

        guardar_settings(nuevo)
        aplicar_settings(nuevo)

        # Sincronizar variables Tkinter de la app principal
        creds = nuevo["credenciales"]
        self.app.var_remitente.set(creds.get("remitente", ""))
        self.app.var_contrasena.set(creds.get("contrasena", ""))
        self.app.var_sheet_id.set(nuevo["sheets"].get("spreadsheet_id", ""))

        self.app.log("✔ Configuración guardada y aplicada.", "ok")
        messagebox.showinfo("Guardado", "Configuración guardada correctamente.", parent=self)
        self.destroy()

    def _restaurar(self):
        if messagebox.askyesno(
            "Restaurar",
            "¿Restaurar todos los campos a los valores por defecto?",
            parent=self,
        ):
            self._settings = copy.deepcopy(DEFAULTS)
            self._poblar()

    def _centrar(self, padre):
        self.update_idletasks()
        x = padre.winfo_x() + (padre.winfo_width()  - self.winfo_width())  // 2
        y = padre.winfo_y() + (padre.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
