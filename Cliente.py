# Cliente de Control para Brazo Robótico LEGO SPIKE Prime
# Punto de entrada de la aplicación

import tkinter as tk
from interfaz import App


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()