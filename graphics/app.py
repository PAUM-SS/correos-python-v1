"""
graphics/app.py
Ventana raíz y orquestador central del sistema.

Responsabilidades:
  - Construir el layout principal (barra, panel izquierdo, panel derecho).
  - Instanciar y conectar todos los paneles.
  - Poseer el estado global compartido (registros, worksheet, flags).
  - Ejecutar las tareas pesadas en hilos secundarios (threading).
  - Delegar la lógica de negocio a los módulos auth/, send/, templates/.
"""

import os
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from config        import COLOR, BATCH_SIZE, EMAIL_DELAY, COLUMN_CONFIG, CREDENTIALS_FILE, TEMPLATE_FILE
from config_manager import cargar_settings, aplicar_settings
from auth          import (
    conectar_google_sheets, obtener_registros_con_folio,
    registrar_documento_generado, registrar_link_drive, registrar_estado_envio,
    subir_pdf,
)
from send          import enviar_correo
from templates     import generar_constancia, generar_nombre_archivo, limpiar_temporales_drive, SESION_CONFIG
from config_manager import cargar_settings
from graphics.styles        import aplicar_estilos
from graphics.panels        import (
    PanelCredenciales,
    PanelSheets,
    PanelControlLote,
    PanelTabla,
    PanelLog,
    VentanaConfiguracion,
)


class AplicacionConstancias(tk.Tk):
    """
    Ventana principal del sistema de emisión de constancias.

    Estado global:
        registros (list[dict]): filas con folio cargadas desde Sheets.
        worksheet:              hoja activa de gspread (None si no conectado).
        enviando (bool):        True mientras haya un lote en proceso.

    Variables Tkinter (accesibles desde los paneles):
        var_remitente, var_contrasena, var_sheet_id, var_progreso
    """

    def __init__(self):
        super().__init__()
        self.title("Emisor de Constancias Corporativas v1.0")
        self.geometry("1100x750")
        self.minsize(900, 650)
        self.configure(bg=COLOR["bg_oscuro"])

        # ── Estado global ─────────────────────────────────────────────────
        self.registros:  list[dict]              = []
        self.worksheet                           = None
        self.enviando:   bool                    = False
        self._hilo_envio: threading.Thread | None = None

        # ── Variables Tkinter (compartidas con paneles) ───────────────────
        self.var_remitente  = tk.StringVar()
        self.var_contrasena = tk.StringVar()
        self.var_sheet_id   = tk.StringVar()
        self.var_progreso   = tk.DoubleVar(value=0)

        # ── Cargar settings guardados ─────────────────────────────────────
        self._cargar_settings_iniciales()

        # ── Inicialización de UI ──────────────────────────────────────────
        aplicar_estilos(self)
        self._construir_layout()
        self._verificar_dependencias_iniciales()

    # ══════════════════════════════════════════════════════════════════════
    #  CONSTRUCCIÓN DEL LAYOUT
    # ══════════════════════════════════════════════════════════════════════

    def _construir_layout(self) -> None:
        C = COLOR

        # ── Barra de título ───────────────────────────────────────────────
        barra = tk.Frame(self, bg=C["bg_panel"], pady=10)
        barra.pack(fill="x")

        tk.Label(
            barra,
            text="📋  Emisor de Constancias Corporativas",
            bg=C["bg_panel"],
            fg=C["texto"],
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left", padx=18)

        self._lbl_estado = tk.Label(
            barra,
            text="● Sin conexión",
            bg=C["bg_panel"],
            fg=C["texto_dim"],
            font=("Segoe UI", 9),
        )
        self._lbl_estado.pack(side="right", padx=18)

        tk.Button(
            barra,
            text="⚙  Configuración",
            bg=C["bg_input"],
            fg=C["texto"],
            font=("Segoe UI", 9),
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            activebackground=C["acento"],
            activeforeground="white",
            command=self._abrir_configuracion,
        ).pack(side="right", padx=(0, 8))

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # ── Contenedor dividido en dos columnas ───────────────────────────
        contenedor = tk.Frame(self, bg=C["bg_oscuro"])
        contenedor.pack(fill="both", expand=True, padx=10, pady=8)

        # Panel izquierdo: configuración (ancho fijo)
        panel_izq = tk.Frame(contenedor, bg=C["bg_oscuro"], width=310)
        panel_izq.pack(side="left", fill="y", padx=(0, 6))
        panel_izq.pack_propagate(False)

        # Panel derecho: tabla + log (expansible)
        panel_der = tk.Frame(contenedor, bg=C["bg_oscuro"])
        panel_der.pack(side="left", fill="both", expand=True)

        # ── Instanciar paneles ────────────────────────────────────────────
        self.panel_credenciales = PanelCredenciales(panel_izq, app=self)
        self.panel_sheets       = PanelSheets(panel_izq, app=self)
        self.panel_lote         = PanelControlLote(panel_izq, app=self)

        self.panel_tabla        = PanelTabla(panel_der, app=self)
        self.panel_log          = PanelLog(panel_der, app=self)

    # ══════════════════════════════════════════════════════════════════════
    #  API PÚBLICA — llamada desde los paneles
    # ══════════════════════════════════════════════════════════════════════

    def log(self, mensaje: str, nivel: str = "info") -> None:
        """Proxy thread-safe hacia PanelLog.escribir()."""
        self.panel_log.escribir(mensaje, nivel)

    def iniciar_carga_datos(self) -> None:
        """Valida y lanza la descarga de datos en un hilo secundario."""
        sheet_id = self.var_sheet_id.get().strip()
        if not sheet_id:
            messagebox.showwarning("Falta el ID", "Ingresa el Spreadsheet ID antes de continuar.")
            return

        self.log("Conectando a Google Sheets…")
        self._set_estado("Conectando…", COLOR["advertencia"])
        threading.Thread(
            target=self._tarea_carga_datos,
            args=(sheet_id,),
            daemon=True,
        ).start()

    def iniciar_envio_lote(self) -> None:
        """Valida y lanza el envío del siguiente lote en un hilo secundario."""
        if self.enviando:
            return
        if not self._validar_para_envio():
            return

        pendientes = [
            (idx, fila) for idx, fila in enumerate(self.registros)
            if fila.get("_estado_local", "listo") == "listo"
        ][:BATCH_SIZE]

        if not pendientes:
            messagebox.showinfo("Sin pendientes", "No hay registros pendientes en este lote.")
            return

        confirmado = messagebox.askyesno(
            "Confirmar Envío",
            f"¿Enviar las próximas {len(pendientes)} constancias?\n\n"
            f"Remitente: {self.var_remitente.get()}\n"
            f"Lote máximo: {BATCH_SIZE} correos",
        )
        if not confirmado:
            return

        self.enviando = True
        self.panel_lote.set_enviando(True)
        self.var_progreso.set(0)

        self._hilo_envio = threading.Thread(
            target=self._tarea_envio_lote,
            args=(pendientes,),
            daemon=True,
        )
        self._hilo_envio.start()

    def detener_envio(self) -> None:
        """Señaliza al hilo de envío que debe detenerse."""
        self.enviando = False
        self.log("Solicitud de detención recibida…", "warn")

    # ══════════════════════════════════════════════════════════════════════
    #  TAREAS EN HILO SECUNDARIO
    # ══════════════════════════════════════════════════════════════════════

    def _tarea_carga_datos(self, sheet_id: str) -> None:
        """Hilo: conecta a Sheets y descarga registros con folio."""
        try:
            self.worksheet = conectar_google_sheets(sheet_id)
            self.log(f"Conectado a: '{self.worksheet.spreadsheet.title}'", "ok")

            # Soporta tanto la versión nueva (retorna tupla) como la vieja (retorna lista)
            resultado = obtener_registros_con_folio(self.worksheet)
            if isinstance(resultado, tuple):
                self.registros, self._reporte_columnas = resultado
            else:
                self.registros          = resultado
                self._reporte_columnas  = {}
            self.after(0, self._on_datos_cargados)

        except FileNotFoundError as e:
            self.log(str(e), "err")
            self.after(0, lambda: messagebox.showerror("credentials.json no encontrado", str(e)))

        except Exception as e:
            self.log(f"Error al cargar datos: {e}", "err")
            self.after(0, lambda: messagebox.showerror("Error de Conexión", str(e)))
            self.after(0, lambda: self._set_estado("● Error de conexión", COLOR["error"]))

    def _tarea_envio_lote(self, pendientes: list[tuple[int, dict]]) -> None:
        """Hilo: genera constancias y envía correos del lote actual."""
        total    = len(pendientes)
        enviados = 0
        fallidos = 0

        # ── Limpiar archivos temporales huérfanos antes de empezar ─────────
        self.log("Limpiando archivos temporales en Drive…", "info")
        try:
            _, msg_limpieza = limpiar_temporales_drive()
            self.log(f"  ♻ {msg_limpieza}", "ok")
        except Exception as e_clean:
            self.log(f"  ⚠ No se pudo limpiar Drive: {e_clean}", "warn")

        self.log(f"Iniciando lote: {total} constancias por enviar.", "info")

        for i, (idx, fila) in enumerate(pendientes):
            if not self.enviando:
                self.log("⛔ Envío detenido por el usuario.", "warn")
                break

            nombre   = str(fila.get(COLUMN_CONFIG.get("nombre",   "Nombres"),   "")).strip()
            apellido = str(fila.get(COLUMN_CONFIG.get("apellido", "Apellidos"), "")).strip()
            email    = str(fila.get(COLUMN_CONFIG.get("email",    "Email"),     "")).strip()
            folio    = str(fila.get(COLUMN_CONFIG.get("folio",    "Folio"),     "")).strip()

            self.log(f"[{i+1}/{total}] '{nombre} {apellido}' | {email} | {folio}")

            if not folio or "/" in folio:
                fallidos += 1; fila["_estado_local"] = "fallido"
                self.after(0, lambda ix=idx: self.panel_tabla.actualizar_fila(ix, "Folio inválido", "fallido"))
                self.log(f"  ⚠ Folio '{folio}' inválido — omitido.", "warn")
                continue

            if not email:
                fallidos += 1; fila["_estado_local"] = "fallido"
                self.after(0, lambda ix=idx: self.panel_tabla.actualizar_fila(ix, "Sin email", "fallido"))
                self.log(f"  ✘ Email vacío. Columnas: {list(fila.keys())[:5]}…", "err")
                continue

            self.after(0, lambda ix=idx: self.panel_tabla.actualizar_fila(ix, "Generando…", "enviando"))

            try:
                cfg        = cargar_settings()
                nombre_pdf = generar_nombre_archivo(fila, cfg)
                pdf_bytes  = generar_constancia(fila)
                self.log(f"  ✔ PDF: {nombre_pdf}", "ok")

                # Subir a Drive
                link_drive = ""
                folder_id  = cfg.get("drive", {}).get("folder_id", "")
                if folder_id:
                    try:
                        self.after(0, lambda ix=idx: self.panel_tabla.actualizar_fila(ix, "Subiendo a Drive…", "enviando"))
                        res = subir_pdf(pdf_bytes, nombre_pdf, folder_id)
                        link_drive = res.get("webViewLink", "")
                        self.log(f"  ☁ Drive: {link_drive}", "ok")
                    except Exception as e_dr:
                        self.log(f"  ⚠ Drive: {e_dr}", "warn")

                # Registrar en Sheets
                if self.worksheet:
                    try:
                        registrar_documento_generado(self.worksheet, folio)
                        if link_drive:
                            registrar_link_drive(self.worksheet, folio, link_drive)
                    except Exception as e_sh:
                        self.log(f"  ⚠ Sheets (generado): {e_sh}", "warn")

                # Enviar correo
                self.after(0, lambda ix=idx: self.panel_tabla.actualizar_fila(ix, "Enviando correo…", "enviando"))
                email_cfg = cfg.get("email_cuerpo", {})
                enviar_correo(
                    remitente=self.var_remitente.get().strip(),
                    contrasena=self.var_contrasena.get().strip(),
                    destinatario=email,
                    nombre=nombre, apellido=apellido, folio=folio,
                    archivo_adjunto=pdf_bytes, nombre_archivo=nombre_pdf,
                    asunto_tpl=email_cfg.get("asunto", "Constancia — Folio {folio}"),
                    html_tpl=email_cfg.get("html", ""),
                )
                enviados += 1; fila["_estado_local"] = "enviado"
                self.after(0, lambda ix=idx: self.panel_tabla.actualizar_fila(ix, "Enviado ✔", "enviado"))
                self.log(f"  ✔ Enviado a {email}", "ok")

                if self.worksheet:
                    try: registrar_estado_envio(self.worksheet, folio, enviado=True)
                    except Exception: pass

            except Exception as e:
                fallidos += 1; fila["_estado_local"] = "fallido"
                self.after(0, lambda ix=idx, er=str(e):
                    self.panel_tabla.actualizar_fila(ix, f"Error: {er[:40]}", "fallido"))
                self.log(f"  ✘ Error con {email}: {e}", "err")
                if self.worksheet:
                    try: registrar_estado_envio(self.worksheet, folio, enviado=False)
                    except Exception: pass

            # Progreso visual
            pct = ((i + 1) / total) * 100
            self.after(0, lambda p=pct, e=enviados, t=total:
                self.panel_lote.actualizar_progreso(p, e, t))

            time.sleep(EMAIL_DELAY)

        self.log(
            f"Lote completado: {enviados} enviados, {fallidos} fallos de {total} intentos.",
            "ok" if fallidos == 0 else "warn",
        )
        self.after(0, self._on_lote_finalizado)

    # ══════════════════════════════════════════════════════════════════════
    #  CALLBACKS (hilo principal, via after())
    # ══════════════════════════════════════════════════════════════════════

    def _on_datos_cargados(self) -> None:
        """Ejecutado en el hilo principal tras cargar datos de Sheets."""
        total = len(self.registros)
        listos, enviados, fallidos = self.panel_tabla.poblar(self.registros)

        self.panel_sheets.actualizar_contador(total)
        self.panel_lote.actualizar_estadisticas(listos, enviados, fallidos)
        self.panel_lote.habilitar_boton_enviar(listos > 0)

        self._set_estado(
            f"● Conectado — {total} registros con folio",
            COLOR["exito"],
        )

        # ── Diagnóstico de columnas ───────────────────────────────────────
        reporte = getattr(self, "_reporte_columnas", {})
        if reporte:
            self.log(f"Encabezados detectados: {reporte.get('encabezados', [])}", "info")
            faltantes = reporte.get("faltantes", {})
            if faltantes:
                for clave, nombre in faltantes.items():
                    self.log(
                        f"  ⚠ Columna '{nombre}' (config['{clave}']) NO encontrada en la hoja. "
                        "Verifica COLUMN_CONFIG en config.py",
                        "warn",
                    )
            else:
                self.log("Todas las columnas de config.py coinciden con la hoja.", "ok")

        if listos > 0:
            self.log(f"Tabla actualizada: {listos} listos, {enviados} enviados, {fallidos} fallidos.", "ok")
        else:
            self.log(
                f"No hay registros con folio válido. "
                f"Total de filas descargadas: {sum(1 for _ in self.registros) if self.registros else 0}. "
                "Revisa los encabezados reportados arriba.",
                "warn",
            )

    def _on_lote_finalizado(self) -> None:
        """Ejecutado en el hilo principal al terminar un lote."""
        self.enviando = False
        self.panel_lote.set_enviando(False)

        pendientes = sum(
            1 for f in self.registros if f.get("_estado_local", "listo") == "listo"
        )
        self.panel_lote.habilitar_boton_enviar(pendientes > 0)

        # Recalcular estadísticas
        listos   = sum(1 for f in self.registros if f.get("_estado_local") == "listo")
        enviados = sum(1 for f in self.registros if f.get("_estado_local") == "enviado")
        fallidos = sum(1 for f in self.registros if f.get("_estado_local") == "fallido")
        self.panel_lote.actualizar_estadisticas(listos, enviados, fallidos)

        if pendientes > 0:
            self.log(f"Quedan {pendientes} registros pendientes. Puedes enviar el siguiente lote.", "info")
        else:
            self.log("✔ Todos los registros han sido procesados.", "ok")

    # ══════════════════════════════════════════════════════════════════════
    #  HELPERS PRIVADOS
    # ══════════════════════════════════════════════════════════════════════

    def _set_estado(self, texto: str, color: str) -> None:
        self._lbl_estado.config(text=texto, fg=color)

    def _validar_para_envio(self) -> bool:
        """
        Verifica que todos los requisitos estén listos antes de enviar.
        Muestra un messagebox descriptivo si algo falta.
        Retorna True si todo está en orden.
        """
        if not self.var_remitente.get().strip():
            messagebox.showwarning("Falta el correo", "Ingresa el correo remitente.")
            return False
        if not self.var_contrasena.get().strip():
            messagebox.showwarning("Falta la contraseña", "Ingresa la contraseña de aplicación.")
            return False
        if not os.path.exists(TEMPLATE_FILE):
            messagebox.showerror(
                "Plantilla no encontrada",
                f"No se encontró '{TEMPLATE_FILE}'.\n"
                "Coloca el archivo .pptx de plantilla en la raíz del proyecto.",
            )
            return False

        # Verificar python-docx en tiempo de ejecución
        try:
            from pptx import Presentation  # noqa: F401
        except ImportError:
            messagebox.showerror(
                "python-pptx no instalado",
                "Instala la librería:\n\npip install python-pptx",
            )
            return False

        return True

    def _cargar_settings_iniciales(self) -> None:
        """Carga settings.json y pre-rellena las variables Tkinter."""
        settings = cargar_settings()
        aplicar_settings(settings)

        creds = settings.get("credenciales", {})
        if creds.get("remitente"):
            self.var_remitente.set(creds["remitente"])
        if creds.get("contrasena"):
            self.var_contrasena.set(creds["contrasena"])

        sheets = settings.get("sheets", {})
        if sheets.get("spreadsheet_id"):
            self.var_sheet_id.set(sheets["spreadsheet_id"])

    def _abrir_configuracion(self) -> None:
        """Abre la ventana modal de configuración."""
        VentanaConfiguracion(self, app=self)

    def _verificar_dependencias_iniciales(self) -> None:
        """Avisa en el log si faltan librerías o archivos de soporte."""
        faltantes = []
        try:
            import gspread          # noqa: F401
            from google.oauth2.service_account import Credentials  # noqa: F401
        except ImportError:
            faltantes.append("gspread google-auth")

        try:
            from pptx import Presentation   # noqa: F401
        except ImportError:
            faltantes.append("python-pptx")

        if faltantes:
            self.log(
                f"⚠ Librerías faltantes → pip install {' '.join(faltantes)}",
                "warn",
            )
        else:
            self.log("Sistema iniciado. Todas las dependencias disponibles.", "ok")

        if not os.path.exists(CREDENTIALS_FILE):
            self.log(f"⚠ No se encontró '{CREDENTIALS_FILE}' (necesario para conectar a Sheets).", "warn")
        if not os.path.exists(TEMPLATE_FILE):
            self.log(f"⚠ No se encontró la plantilla '{TEMPLATE_FILE}'.", "warn")