"""
graphics/styles.py
Centraliza toda la configuración visual de ttk.Style.
Llamar a aplicar_estilos(root) una sola vez al iniciar la app.
"""

from tkinter import ttk
from config import COLOR


def aplicar_estilos(root) -> None:
    """
    Configura el tema ttk y todos los estilos personalizados del proyecto.

    Args:
        root: instancia tk.Tk sobre la que se aplica el tema.
    """
    style = ttk.Style(root)
    style.theme_use("clam")

    C = COLOR

    # ── Contenedores ──────────────────────────────────────────────────────
    style.configure("TFrame",      background=C["bg_panel"])
    style.configure("Dark.TFrame", background=C["bg_oscuro"])

    # ── Etiquetas ─────────────────────────────────────────────────────────
    style.configure(
        "TLabel",
        background=C["bg_panel"],
        foreground=C["texto"],
        font=("Segoe UI", 9),
    )
    style.configure(
        "Header.TLabel",
        background=C["bg_oscuro"],
        foreground=C["texto"],
        font=("Segoe UI", 13, "bold"),
    )
    style.configure(
        "Sub.TLabel",
        background=C["bg_panel"],
        foreground=C["texto_dim"],
        font=("Segoe UI", 8),
    )

    # ── Entradas ──────────────────────────────────────────────────────────
    style.configure(
        "TEntry",
        fieldbackground=C["bg_input"],
        foreground=C["texto"],
        insertcolor=C["texto"],
        bordercolor=C["borde"],
        lightcolor=C["borde"],
        darkcolor=C["borde"],
        font=("Segoe UI", 9),
    )

    # ── Botón primario (azul) ─────────────────────────────────────────────
    style.configure(
        "Primary.TButton",
        background=C["acento"],
        foreground="white",
        font=("Segoe UI", 9, "bold"),
        borderwidth=0,
        focusthickness=0,
        padding=(12, 6),
    )
    style.map(
        "Primary.TButton",
        background=[("active", C["acento_hover"]), ("disabled", C["borde"])],
        foreground=[("disabled", C["texto_dim"])],
    )

    # ── Botón éxito (verde) ───────────────────────────────────────────────
    style.configure(
        "Success.TButton",
        background=C["exito"],
        foreground="white",
        font=("Segoe UI", 9, "bold"),
        borderwidth=0,
        focusthickness=0,
        padding=(12, 6),
    )
    style.map(
        "Success.TButton",
        background=[("active", "#2ECC71"), ("disabled", C["borde"])],
        foreground=[("disabled", C["texto_dim"])],
    )

    # ── Botón peligro (rojo) ──────────────────────────────────────────────
    style.configure(
        "Danger.TButton",
        background=C["error"],
        foreground="white",
        font=("Segoe UI", 9, "bold"),
        borderwidth=0,
        focusthickness=0,
        padding=(12, 6),
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#C0392B"), ("disabled", C["borde"])],
        foreground=[("disabled", C["texto_dim"])],
    )

    # ── Treeview ──────────────────────────────────────────────────────────
    style.configure(
        "Treeview",
        background=C["bg_input"],
        foreground=C["texto"],
        fieldbackground=C["bg_input"],
        rowheight=26,
        font=("Segoe UI", 9),
    )
    style.configure(
        "Treeview.Heading",
        background=C["bg_panel"],
        foreground=C["acento"],
        font=("Segoe UI", 9, "bold"),
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", C["acento"])],
        foreground=[("selected", "white")],
    )

    # ── Barra de progreso ─────────────────────────────────────────────────
    style.configure(
        "TProgressbar",
        troughcolor=C["bg_input"],
        background=C["acento"],
        thickness=8,
    )

    # ── Separador ─────────────────────────────────────────────────────────
    style.configure("TSeparator", background=C["borde"])
