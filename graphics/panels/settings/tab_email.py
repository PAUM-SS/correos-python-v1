"""
graphics/panels/settings/tab_email.py
Pestaña 📧 Correo:
  - Campo de asunto (con variables {nombre}, {apellido}, {folio})
  - Editor de texto enriquecido: negrita, cursiva, subrayado
  - Serialización a HTML para el envío

El HTML se guarda en settings.json → email_cuerpo → html.
Las variables {nombre}, {apellido}, {folio} se sustituyen al enviar.
"""

import html as _html_mod
import tkinter as tk
from tkinter import ttk, font as tkfont

from config import COLOR

_FONT_FAMILY = "Segoe UI"
_FONT_SIZE   = 10


class TabEmail(tk.Frame):

    def __init__(self, padre, vars_: dict):
        """
        vars_: debe tener 'asunto' (StringVar).
        El contenido del editor se maneja internamente y se accede via recoger().
        """
        super().__init__(padre, bg=COLOR["bg_panel"], padx=16, pady=14)
        self._vars = vars_
        self._construir()

    # ══════════════════════════════════════════════════════════════════════
    #  CONSTRUCCIÓN
    # ══════════════════════════════════════════════════════════════════════

    def _construir(self):
        C = COLOR
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        # Asunto
        ttk.Label(self, text="Asunto del correo:").grid(row=0, column=0, sticky="w")
        ttk.Entry(self, textvariable=self._vars["asunto"], width=55).grid(
            row=1, column=0, sticky="ew", pady=(2, 0))

        ttk.Label(
            self,
            text="Variables disponibles: {nombre}  {apellido}  {folio}",
            style="Sub.TLabel",
        ).grid(row=2, column=0, sticky="w", pady=(2, 8))

        # Barra de herramientas de formato
        barra = tk.Frame(self, bg=C["bg_input"], pady=4, padx=4)
        barra.grid(row=3, column=0, sticky="ew")
        self._crear_barra(barra)

        # Área de texto
        frame_txt = tk.Frame(self, bg=C["borde"])
        frame_txt.grid(row=4, column=0, sticky="nsew", pady=(2, 0))
        frame_txt.columnconfigure(0, weight=1)
        frame_txt.rowconfigure(0, weight=1)

        self._txt = tk.Text(
            frame_txt,
            bg=C["bg_input"], fg=C["texto"],
            font=(_FONT_FAMILY, _FONT_SIZE),
            insertbackground=C["texto"],
            wrap="word", bd=0, padx=8, pady=6,
            undo=True,
            height=12,
        )
        scroll = ttk.Scrollbar(frame_txt, command=self._txt.yview)
        self._txt.configure(yscrollcommand=scroll.set)
        self._txt.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        # Configurar tags de formato
        self._txt.tag_configure("bold",      font=(_FONT_FAMILY, _FONT_SIZE, "bold"))
        self._txt.tag_configure("italic",    font=(_FONT_FAMILY, _FONT_SIZE, "italic"))
        self._txt.tag_configure("underline", underline=True)
        self._txt.tag_configure("bold_italic", font=(_FONT_FAMILY, _FONT_SIZE, "bold italic"))

    def _crear_barra(self, barra: tk.Frame):
        C = COLOR

        def boton(texto, tag, tooltip=""):
            b = tk.Button(
                barra, text=texto,
                bg=C["bg_panel"], fg=C["texto"],
                font=(_FONT_FAMILY, 9, "bold"),
                bd=0, padx=8, pady=2,
                cursor="hand2",
                activebackground=C["acento"],
                activeforeground="white",
                command=lambda t=tag: self._toggle_tag(t),
            )
            b.pack(side="left", padx=2)
            return b

        boton("N",  "bold")
        boton("C",  "italic")
        boton("S",  "underline")

        tk.Label(barra, text="  |  ", bg=COLOR["bg_input"],
                 fg=COLOR["borde"]).pack(side="left")

        tk.Button(
            barra, text="Limpiar formato",
            bg=COLOR["bg_panel"], fg=COLOR["texto_dim"],
            font=(_FONT_FAMILY, 8), bd=0, padx=6, pady=2,
            cursor="hand2",
            command=self._limpiar_formato,
        ).pack(side="left", padx=2)

        tk.Label(
            barra,
            text="  N=negrita  C=cursiva  S=subrayado",
            bg=COLOR["bg_input"], fg=COLOR["texto_dim"],
            font=(_FONT_FAMILY, 7),
        ).pack(side="right", padx=6)

    # ══════════════════════════════════════════════════════════════════════
    #  FORMATO
    # ══════════════════════════════════════════════════════════════════════

    def _toggle_tag(self, tag: str):
        """Aplica o quita el tag en la selección actual."""
        try:
            sel_start = self._txt.index("sel.first")
            sel_end   = self._txt.index("sel.last")
        except tk.TclError:
            return  # sin selección

        tags_actuales = self._txt.tag_names(sel_start)
        if tag in tags_actuales:
            self._txt.tag_remove(tag, sel_start, sel_end)
        else:
            self._txt.tag_add(tag, sel_start, sel_end)

    def _limpiar_formato(self):
        try:
            s = self._txt.index("sel.first")
            e = self._txt.index("sel.last")
        except tk.TclError:
            s, e = "1.0", "end"
        for tag in ("bold", "italic", "underline", "bold_italic"):
            self._txt.tag_remove(tag, s, e)

    # ══════════════════════════════════════════════════════════════════════
    #  SERIALIZACIÓN HTML
    # ══════════════════════════════════════════════════════════════════════

    def obtener_html(self) -> str:
        """
        Convierte el contenido del editor a HTML.
        Normaliza líneas en blanco consecutivas a máximo una línea vacía
        para evitar exceso de espacios en el correo recibido.
        """
        import re as _re
        txt = self._txt
        content = txt.get("1.0", "end-1c")
        if not content:
            return ""

        resultado = []
        idx = "1.0"

        while txt.compare(idx, "<", "end-1c"):
            char      = txt.get(idx, f"{idx} +1c")
            tags      = set(txt.tag_names(idx))
            siguiente = f"{idx} +1c"

            if char == "\n":
                resultado.append("<br>\n")
            else:
                char_html = _html_mod.escape(char)
                if "underline" in tags:
                    char_html = f"<u>{char_html}</u>"
                if "italic" in tags:
                    char_html = f"<i>{char_html}</i>"
                if "bold" in tags:
                    char_html = f"<b>{char_html}</b>"
                resultado.append(char_html)

            idx = siguiente

        html_str = "".join(resultado)
        # Colapsar 3+ <br> consecutivos → máximo 2 (un salto de párrafo)
        html_str = _re.sub(r'(<br>\n){3,}', '<br>\n<br>\n', html_str)
        return html_str

    def cargar_html(self, html_str: str):
        """
        Carga HTML básico en el editor de texto.
        Soporta: <b>, <i>, <u>, <br>, texto plano.
        """
        self._txt.delete("1.0", "end")
        if not html_str:
            return

        import re
        # <p> → párrafo con línea en blanco; </p> se elimina
        txt = re.sub(r'<p[^>]*>', '', html_str, flags=re.IGNORECASE)
        txt = re.sub(r'</p>', '\n', txt, flags=re.IGNORECASE)
        # <br> → salto de línea simple
        txt = re.sub(r'<br\s*/?>', '\n', txt, flags=re.IGNORECASE)
        # Eliminar otras etiquetas no soportadas
        txt = re.sub(r'<(?!/?(?:b|i|u)\b)[^>]+>', '', txt)
        # Normalizar: 3+ saltos de línea → máximo 2
        txt = re.sub(r'\n{3,}', '\n\n', txt)

        # Parsear segmentos con tags
        patron = re.compile(r'(</?(?:b|i|u)>)', re.IGNORECASE)
        partes = patron.split(txt)

        tags_activos = set()
        for parte in partes:
            parte_low = parte.lower()
            if   parte_low == "<b>":  tags_activos.add("bold")
            elif parte_low == "</b>": tags_activos.discard("bold")
            elif parte_low == "<i>":  tags_activos.add("italic")
            elif parte_low == "</i>": tags_activos.discard("italic")
            elif parte_low == "<u>":  tags_activos.add("underline")
            elif parte_low == "</u>": tags_activos.discard("underline")
            else:
                # Es texto real
                decoded = _html_mod.unescape(parte)
                if decoded:
                    pos_ini = self._txt.index("end-1c")
                    self._txt.insert("end", decoded)
                    pos_fin = self._txt.index("end-1c")
                    for tag in tags_activos:
                        self._txt.tag_add(tag, pos_ini, pos_fin)

    # ══════════════════════════════════════════════════════════════════════
    #  API PÚBLICA
    # ══════════════════════════════════════════════════════════════════════

    def recoger(self) -> dict:
        return {
            "asunto": self._vars["asunto"].get().strip(),
            "html":   self.obtener_html(),
        }

    def poblar(self, asunto: str, html: str):
        self._vars["asunto"].set(asunto)
        self.cargar_html(html)