# """
# graphics/panels/message_editor.py
# Panel para editar y previsualizar el mensaje del correo electrónico.
# """

# import tkinter as tk
# from tkinter import ttk, scrolledtext, messagebox
# from config import COLOR


# class PanelMessageEditor(tk.Frame):
#     """Panel que permite editar el mensaje del correo y previsualizarlo."""
    
#     def __init__(self, parent, app=None, **kwargs):
#         super().__init__(parent, **kwargs)
#         self.app = app
#         self.configure(bg=COLOR["bg_oscuro"])
        
#         # Variables
#         self.preview_window = None
        
#         # Construir UI
#         self._construir_panel()
#         self._cargar_mensaje_guardado()
    
#     def _construir_panel(self):
#         """Construye los elementos del panel."""
#         # Frame contenedor con borde
#         frame = tk.LabelFrame(
#             self,
#             text="📝 Editor de Mensaje",
#             bg=COLOR["bg_panel"],
#             fg=COLOR["texto"],
#             font=("Segoe UI", 10, "bold"),
#             padx=10,
#             pady=5
#         )
#         frame.pack(fill="both", expand=True, padx=10, pady=5)
        
#         # Botones de acción
#         botones_frame = tk.Frame(frame, bg=COLOR["bg_panel"])
#         botones_frame.pack(fill="x", pady=(0, 5))
        
#         # Botón de previsualización
#         self.btn_preview = tk.Button(
#             botones_frame,
#             text="👁️ Vista Previa",
#             bg=COLOR["acento"],
#             fg="white",
#             font=("Segoe UI", 9),
#             bd=0,
#             padx=10,
#             pady=4,
#             cursor="hand2",
#             command=self._mostrar_previsualizacion
#         )
#         self.btn_preview.pack(side="left", padx=(0, 5))
        
#         # Botón de restablecer predeterminado
#         self.btn_reset = tk.Button(
#             botones_frame,
#             text="⟳ Restablecer",
#             bg=COLOR["bg_input"],
#             fg=COLOR["texto"],
#             font=("Segoe UI", 9),
#             bd=0,
#             padx=10,
#             pady=4,
#             cursor="hand2",
#             command=self._resetear_mensaje
#         )
#         self.btn_reset.pack(side="left")
        
#         # Área de texto para el mensaje
#         label = tk.Label(
#             frame,
#             text="Contenido del mensaje:",
#             bg=COLOR["bg_panel"],
#             fg=COLOR["texto"],
#             font=("Segoe UI", 9),
#             anchor="w"
#         )
#         label.pack(anchor="w", pady=(5, 0))
        
#         # ScrolledText para edición
#         self.text_area = scrolledtext.ScrolledText(
#             frame,
#             wrap=tk.WORD,
#             width=50,
#             height=12,
#             bg=COLOR["bg_input"],
#             fg=COLOR["texto"],
#             font=("Segoe UI", 9),
#             insertbackground=COLOR["texto"]
#         )
#         self.text_area.pack(fill="both", expand=True, pady=(5, 10))
        
#         # Frame para variables dinámicas
#         vars_frame = tk.Frame(frame, bg=COLOR["bg_panel"])
#         vars_frame.pack(fill="x", pady=(0, 5))
        
#         tk.Label(
#             vars_frame,
#             text="💡 Variables disponibles:",
#             bg=COLOR["bg_panel"],
#             fg=COLOR["texto_dim"],
#             font=("Segoe UI", 8, "italic")
#         ).pack(anchor="w")
        
#         tk.Label(
#             vars_frame,
#             text="{nombre} - Nombre del destinatario | {folio} - Número de folio",
#             bg=COLOR["bg_panel"],
#             fg=COLOR["texto_dim"],
#             font=("Segoe UI", 8)
#         ).pack(anchor="w", pady=(2, 0))
        
#         # Botón para guardar mensaje
#         self.btn_save = tk.Button(
#             frame,
#             text="💾 Guardar Mensaje",
#             bg=COLOR["exito"],
#             fg="white",
#             font=("Segoe UI", 9),
#             bd=0,
#             padx=10,
#             pady=4,
#             cursor="hand2",
#             command=self._guardar_mensaje
#         )
#         self.btn_save.pack(pady=(0, 5))
        
#         # Tooltip informativo
#         self._crear_tooltip()
    
#     def _crear_tooltip(self):
#         """Crea tooltip informativo para el botón de previsualización."""
#         def show_tooltip(event):
#             tooltip = tk.Toplevel(self)
#             tooltip.wm_overrideredirect(True)
#             tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
#             label = tk.Label(
#                 tooltip,
#                 text="Previsualiza el mensaje con los valores de ejemplo",
#                 bg="#ffffcc",
#                 fg="#000000",
#                 relief="solid",
#                 borderwidth=1,
#                 font=("Segoe UI", 8)
#             )
#             label.pack()
            
#             def hide_tooltip():
#                 tooltip.destroy()
            
#             self.btn_preview.bind("<Leave>", lambda e: hide_tooltip())
        
#         self.btn_preview.bind("<Enter>", show_tooltip)
    
#     def _cargar_mensaje_guardado(self):
#         """Carga el mensaje guardado desde settings.json."""
#         try:
#             from config_manager import cargar_settings
#             settings = cargar_settings()
#             mensaje = settings.get("mensaje_personalizado", "")
            
#             if mensaje:
#                 # Limpiar y cargar el mensaje guardado
#                 self.text_area.delete("1.0", tk.END)
#                 self.text_area.insert("1.0", mensaje)
#             else:
#                 # Cargar mensaje predeterminado
#                 self._resetear_mensaje()
#         except Exception as e:
#             self._resetear_mensaje()
    
#     def _resetear_mensaje(self):
#         """Restablece el mensaje al texto predeterminado."""
#         mensaje_default = (
#             "Estimado/a {nombre},\n\n"
#             "Adjunto encontrará su constancia de participación con el folio {folio}.\n\n"
#             "Si tiene alguna pregunta, no dude en contactarnos.\n\n"
#             "Atentamente,\n"
#             "Departamento de Recursos Humanos"
#         )
#         self.text_area.delete("1.0", tk.END)
#         self.text_area.insert("1.0", mensaje_default)
    
#     def _guardar_mensaje(self):
#         """Guarda el mensaje actual en settings.json."""
#         try:
#             from config_manager import cargar_settings, guardar_settings
#             mensaje = self.text_area.get("1.0", tk.END).strip()
            
#             if mensaje:
#                 settings = cargar_settings()
#                 settings["mensaje_personalizado"] = mensaje
#                 guardar_settings(settings)
                
#                 # También actualizar en el módulo de envío si es posible
#                 try:
#                     from send import set_custom_message
#                     set_custom_message(mensaje)
#                 except:
#                     pass
                
#                 messagebox.showinfo("Éxito", "Mensaje guardado correctamente")
#             else:
#                 messagebox.showwarning("Advertencia", "El mensaje no puede estar vacío")
#         except Exception as e:
#             messagebox.showerror("Error", f"No se pudo guardar el mensaje: {e}")
    
#     def _mostrar_previsualizacion(self):
#         """Muestra una ventana con la previsualización del mensaje."""
#         if self.preview_window and self.preview_window.winfo_exists():
#             self.preview_window.lift()
#             return
        
#         # Crear ventana de previsualización
#         self.preview_window = tk.Toplevel(self)
#         self.preview_window.title("Vista Previa del Mensaje")
#         self.preview_window.geometry("600x500")
#         self.preview_window.configure(bg=COLOR["bg_oscuro"])
        
#         # Centrar ventana
#         self.preview_window.transient(self)
#         self.preview_window.grab_set()
        
#         # Frame principal
#         main_frame = tk.Frame(self.preview_window, bg=COLOR["bg_oscuro"])
#         main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
#         # Datos de ejemplo para previsualización
#         tk.Label(
#             main_frame,
#             text="📧 Vista Previa del Correo",
#             bg=COLOR["bg_oscuro"],
#             fg=COLOR["texto"],
#             font=("Segoe UI", 12, "bold")
#         ).pack(pady=(0, 10))
        
#         # Frame para datos de ejemplo
#         ejemplo_frame = tk.LabelFrame(
#             main_frame,
#             text="Datos de ejemplo",
#             bg=COLOR["bg_panel"],
#             fg=COLOR["texto"],
#             font=("Segoe UI", 9)
#         )
#         ejemplo_frame.pack(fill="x", pady=(0, 10), padx=10)
        
#         # Variables de ejemplo editables
#         tk.Label(
#             ejemplo_frame,
#             text="Nombre de ejemplo:",
#             bg=COLOR["bg_panel"],
#             fg=COLOR["texto"]
#         ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
#         self.ejemplo_nombre = tk.Entry(
#             ejemplo_frame,
#             bg=COLOR["bg_input"],
#             fg=COLOR["texto"],
#             width=30
#         )
#         self.ejemplo_nombre.grid(row=0, column=1, padx=5, pady=5)
#         self.ejemplo_nombre.insert(0, "María González")
        
#         tk.Label(
#             ejemplo_frame,
#             text="Folio de ejemplo:",
#             bg=COLOR["bg_panel"],
#             fg=COLOR["texto"]
#         ).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
#         self.ejemplo_folio = tk.Entry(
#             ejemplo_frame,
#             bg=COLOR["bg_input"],
#             fg=COLOR["texto"],
#             width=30
#         )
#         self.ejemplo_folio.grid(row=1, column=1, padx=5, pady=5)
#         self.ejemplo_folio.insert(0, "2024-001")
        
#         # Botón para actualizar vista previa
#         tk.Button(
#             ejemplo_frame,
#             text="Actualizar Vista Previa",
#             command=self._actualizar_vista_previa,
#             bg=COLOR["acento"],
#             fg="white",
#             cursor="hand2"
#         ).grid(row=2, column=0, columnspan=2, pady=10)
        
#         # Área de vista previa
#         preview_label = tk.Label(
#             main_frame,
#             text="Vista previa del mensaje:",
#             bg=COLOR["bg_oscuro"],
#             fg=COLOR["texto"],
#             font=("Segoe UI", 9, "bold")
#         )
#         preview_label.pack(anchor="w", pady=(10, 5))
        
#         # Text widget para mostrar la vista previa
#         self.preview_text = scrolledtext.ScrolledText(
#             main_frame,
#             wrap=tk.WORD,
#             width=60,
#             height=15,
#             bg=COLOR["bg_input"],
#             fg=COLOR["texto"],
#             font=("Segoe UI", 9),
#             state="disabled"
#         )
#         self.preview_text.pack(fill="both", expand=True, padx=10)
        
#         # Mostrar vista previa inicial
#         self._actualizar_vista_previa()
    
#     def _actualizar_vista_previa(self):
#         """Actualiza el texto de vista previa con los valores de ejemplo."""
#         # Obtener mensaje original
#         mensaje_original = self.text_area.get("1.0", tk.END).strip()
        
#         # Reemplazar variables
#         nombre = self.ejemplo_nombre.get().strip() or "[Nombre]"
#         folio = self.ejemplo_folio.get().strip() or "[Folio]"
        
#         mensaje_vista = mensaje_original.replace("{nombre}", nombre)
#         mensaje_vista = mensaje_vista.replace("{folio}", folio)
        
#         # Actualizar en el widget
#         self.preview_text.configure(state="normal")
#         self.preview_text.delete("1.0", tk.END)
#         self.preview_text.insert("1.0", mensaje_vista)
#         self.preview_text.configure(state="disabled")
    
#     def get_mensaje(self, nombre: str = None, folio: str = None) -> str:
#         """
#         Retorna el mensaje con las variables reemplazadas.
        
#         Args:
#             nombre: Nombre del destinatario (reemplaza {nombre})
#             folio: Número de folio (reemplaza {folio})
        
#         Returns:
#             str: Mensaje procesado con los reemplazos
#         """
#         mensaje = self.text_area.get("1.0", tk.END).strip()
        
#         if nombre:
#             mensaje = mensaje.replace("{nombre}", nombre)
#         if folio:
#             mensaje = mensaje.replace("{folio}", str(folio))
        
#         return mensaje