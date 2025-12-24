# Interfaz gráfica para el control del brazo robótico
# Diseño de ventana con paneles de control para cada motor

import tkinter as tk
from tkinter import messagebox
from controlador import RobotController


class App:
    """Ventana principal de control del brazo robótico."""
    
    # Paleta de colores
    BG_DARK = "#1a1a2e"
    BG_PANEL = "#16213e"
    BG_HEADER = "#0f3460"
    ACCENT = "#e94560"
    SUCCESS = "#00d26a"
    WARNING = "#ffc107"
    TEXT = "#ffffff"
    TEXT_DIM = "#a0a0a0"

    def __init__(self, root):
        self.root = root
        self.root.title("Control Brazo Robótico")
        self.root.geometry("520x720")
        self.root.configure(bg=self.BG_DARK)
        self.root.resizable(False, False)

        self.robot = RobotController()
        self.active_keys = set()
        self.buttons = {}

        self._crear_header()
        self._crear_boton_conexion()
        self._crear_paneles_motores()
        self._crear_footer()
        self._configurar_teclado()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _crear_header(self):
        header = tk.Frame(self.root, bg=self.BG_HEADER, pady=15)
        header.pack(fill="x")

        tk.Label(
            header, text="🤖 CONTROL BRAZO ROBÓTICO",
            font=("Segoe UI", 18, "bold"), fg=self.TEXT, bg=self.BG_HEADER
        ).pack()

        self.lbl_status = tk.Label(
            header, text="⚫ DESCONECTADO",
            font=("Segoe UI", 11), fg=self.ACCENT, bg=self.BG_HEADER
        )
        self.lbl_status.pack(pady=(5, 0))

    def _crear_boton_conexion(self):
        self.btn_connect = tk.Button(
            self.root, text="⚡ CONECTAR ROBOT",
            font=("Segoe UI", 12, "bold"),
            bg=self.SUCCESS, fg=self.BG_DARK,
            activebackground="#00b359", activeforeground=self.TEXT,
            cursor="hand2", relief="flat", height=2,
            command=self.do_connect
        )
        self.btn_connect.pack(fill="x", padx=25, pady=15)

    def _crear_paneles_motores(self):
        self.controls_frame = tk.Frame(self.root, bg=self.BG_DARK)
        self.controls_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # (nombre, puerto, tecla1, texto1, cmd1, release1, tecla2, texto2, cmd2, release2, color)
        motores = [
            ("Brazo Principal", "Motor B", "W", "SUBIR", "w", "e", "S", "BAJAR", "s", "e", "#3498db"),
            ("Base Giratoria", "Motor A", "A", "HORARIO", "a", "q", "D", "ANTI-HORARIO", "d", "q", "#e67e22"),
            ("Pinza", "Motor C", "O", "ABRIR", "o", "z", "C", "CERRAR", "c", "z", "#2ecc71"),
            ("Elevador Muñeca", "Motor E", "I", "SUBIR", "i", "m", "K", "BAJAR", "k", "m", "#9b59b6"),
        ]

        for motor in motores:
            self._crear_panel(*motor)

    def _crear_panel(self, titulo, subtitulo, key1, txt1, cmd1_p, cmd1_r, key2, txt2, cmd2_p, cmd2_r, color):
        frame = tk.Frame(self.controls_frame, bg=self.BG_PANEL, pady=10, padx=10)
        frame.pack(fill="x", pady=6)

        # Título del panel
        header_frame = tk.Frame(frame, bg=self.BG_PANEL)
        header_frame.pack(fill="x", pady=(0, 8))

        tk.Label(
            header_frame, text=titulo,
            font=("Segoe UI", 11, "bold"), fg=self.TEXT, bg=self.BG_PANEL
        ).pack(side="left")

        tk.Label(
            header_frame, text=f"({subtitulo})",
            font=("Segoe UI", 9), fg=self.TEXT_DIM, bg=self.BG_PANEL
        ).pack(side="left", padx=(8, 0))

        # Botones de acción
        btn_frame = tk.Frame(frame, bg=self.BG_PANEL)
        btn_frame.pack(fill="x")

        btn1 = tk.Button(
            btn_frame, text=f"[{key1}] {txt1}",
            bg=color, fg="white",
            activebackground=self._oscurecer(color), activeforeground="white",
            font=("Segoe UI", 10, "bold"), height=2,
            relief="flat", cursor="hand2"
        )
        btn1.pack(side="left", expand=True, fill="x", padx=(0, 5))
        btn1.bind('<ButtonPress-1>', lambda e: self._on_press(cmd1_p, btn1, color))
        btn1.bind('<ButtonRelease-1>', lambda e: self._on_release(cmd1_r, btn1, color))

        btn2 = tk.Button(
            btn_frame, text=f"[{key2}] {txt2}",
            bg=color, fg="white",
            activebackground=self._oscurecer(color), activeforeground="white",
            font=("Segoe UI", 10, "bold"), height=2,
            relief="flat", cursor="hand2"
        )
        btn2.pack(side="right", expand=True, fill="x", padx=(5, 0))
        btn2.bind('<ButtonPress-1>', lambda e: self._on_press(cmd2_p, btn2, color))
        btn2.bind('<ButtonRelease-1>', lambda e: self._on_release(cmd2_r, btn2, color))

        # Guardar referencia para el control por teclado
        self.buttons[key1.lower()] = (btn1, cmd1_p, cmd1_r, color)
        self.buttons[key2.lower()] = (btn2, cmd2_p, cmd2_r, color)

    def _crear_footer(self):
        footer = tk.Frame(self.root, bg=self.BG_PANEL, pady=8)
        footer.pack(fill="x", side="bottom")
        tk.Label(
            footer,
            text="💡 Usa el teclado: W/S (brazo) · A/D (base) · O/C (pinza) · I/K (elevador)",
            font=("Segoe UI", 9), fg=self.TEXT_DIM, bg=self.BG_PANEL
        ).pack()

    def _oscurecer(self, hex_color, factor=0.7):
        hex_color = hex_color.lstrip('#')
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _on_press(self, cmd, btn, original_color):
        self.robot.send(cmd)
        btn.config(bg=self._oscurecer(original_color, 0.6))

    def _on_release(self, cmd, btn, original_color):
        self.robot.send(cmd)
        btn.config(bg=original_color)

    def _configurar_teclado(self):
        self.root.bind('<KeyPress>', self._key_press)
        self.root.bind('<KeyRelease>', self._key_release)

    def _key_press(self, event):
        key = event.keysym.lower()
        if key in self.buttons and key not in self.active_keys:
            self.active_keys.add(key)
            btn, cmd_p, cmd_r, color = self.buttons[key]
            self._on_press(cmd_p, btn, color)

    def _key_release(self, event):
        key = event.keysym.lower()
        if key in self.buttons and key in self.active_keys:
            self.active_keys.discard(key)
            btn, cmd_p, cmd_r, color = self.buttons[key]
            self._on_release(cmd_r, btn, color)

    def do_connect(self):
        self.lbl_status.config(text="🔍 BUSCANDO ROBOT...", fg=self.WARNING)
        self.btn_connect.config(state="disabled", bg="#555555")
        self.robot.connect(
            on_success=lambda: self.root.after(0, self.on_success),
            on_error=lambda msg: self.root.after(0, self.on_error, msg),
        )

    def on_success(self):
        self.lbl_status.config(text="🟢 CONECTADO Y LISTO", fg=self.SUCCESS)
        self.btn_connect.config(text="✓ ROBOT CONECTADO", bg="#555555", state="disabled")
        messagebox.showinfo(
            "Éxito", 
            "Robot conectado.\nEl programa fue transferido correctamente.\n\nUsa los botones o el teclado para controlar."
        )

    def on_error(self, err_msg):
        self.lbl_status.config(text="🔴 ERROR DE CONEXIÓN", fg=self.ACCENT)
        self.btn_connect.config(state="normal", text="⚡ CONECTAR ROBOT", bg=self.SUCCESS)
        messagebox.showerror("Error", f"Fallo al conectar:\n{err_msg}")

    def on_close(self):
        self.robot.close()
        self.root.destroy()
