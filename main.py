"""
main.py — Punto de entrada del sistema de emisión de constancias.

Uso:
    python main.py

Dependencias (instalar una sola vez):
    pip install gspread google-auth python-docx
"""

from graphics import AplicacionConstancias


def main() -> None:
    app = AplicacionConstancias()
    app.mainloop()


if __name__ == "__main__":
    main()
