import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import tempfile
import os
from pybricksdev.ble import find_device
from pybricksdev.connections.pybricks import PybricksHubBLE


# Configuración
FIND_DEVICE_TIMEOUT_S = 20
CONNECT_TIMEOUT_S = 20
RUN_PROGRAM_TIMEOUT_S = 30
HUB_NAME = "PY-SC"


# 1. EL CEREBRO DEL ROBOT 
HUB_PROGRAM = """
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Color
from pybricks.tools import wait
from usys import stdin
import uselect

# Inicialización
hub = PrimeHub()
hub.light.on(Color.RED) # Rojo = Cargando

# Configuración de Motores (A, B, C, E)
try: m_base = Motor(Port.A)
except: m_base = None

try: m_brazo = Motor(Port.B)
except: m_brazo = None

try: m_pinza = Motor(Port.C)
except: m_pinza = None

try: m_elev = Motor(Port.E)
except: m_elev = None

hub.light.on(Color.GREEN) # Verde = Listo

while True:
    # Espera datos del PC
    if uselect.select([stdin], [], [], 0)[0]:
        cmd = stdin.read(1)
        
        # --- BASE (A) ---
        if cmd == "a" and m_base: m_base.run(-200)
        elif cmd == "d" and m_base: m_base.run(200)
        elif cmd == "q" and m_base: m_base.stop()
            
        # --- BRAZO (B) 

        elif cmd == "w" and m_brazo: m_brazo.run(-200)
        elif cmd == "s" and m_brazo: m_brazo.run(200)
        elif cmd == "e" and m_brazo: m_brazo.hold()
            
        # --- PINZA (C) 

        elif cmd == "o" and m_pinza: m_pinza.run(-100)
        elif cmd == "c" and m_pinza: m_pinza.run(100)
        elif cmd == "z" and m_pinza: m_pinza.stop()
            
        # --- ELEVADOR (E) ---
        elif cmd == "i" and m_elev: m_elev.run(100)
        elif cmd == "k" and m_elev: m_elev.run(-100)
        elif cmd == "m" and m_elev: m_elev.hold()
        
    wait(10)
"""

# 2. MOTOR DE CONEXIÓN

class RobotController:
    def __init__(self):
        self.hub = None
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.connected = False
        self._closing = False

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect(self, on_success, on_error):
        if self._closing:
            on_error("El controlador está cerrándose.")
            return
        asyncio.run_coroutine_threadsafe(self._connect_task(on_success, on_error), self.loop)

    async def _connect_task(self, on_success, on_error):
        temp_path = None
        try:
            print("🔍 Buscando robot...")
            # Buscar por nombre lo hace más rápido y evita conectar al hub equivocado.
            device = await find_device(name=HUB_NAME, timeout=FIND_DEVICE_TIMEOUT_S)
            if not device:
                on_error("No se encontró ningún Hub encendido.")
                return

            print(f"✅ Encontrado: {device.name}")
            self.hub = PybricksHubBLE(device)
            await asyncio.wait_for(self.hub.connect(), timeout=CONNECT_TIMEOUT_S)
            
            print("🚀 Creando archivo temporal e inyectando código...")
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tf:
                tf.write(HUB_PROGRAM)
                temp_path = tf.name
            
            await asyncio.wait_for(self.hub.run(temp_path, wait=False), timeout=RUN_PROGRAM_TIMEOUT_S)
            
            self.connected = True
            print("🤖 ¡Sistema Listo! Control activado.")
            on_success()
            
        except asyncio.TimeoutError:
            on_error("Tiempo de espera agotado. Verifica que el Hub esté encendido y en modo Pybricks.")

        except Exception as e:
            print(f"Error: {e}")
            on_error(str(e))
        
        finally:
            if temp_path and os.path.exists(temp_path):
                try: os.unlink(temp_path)
                except: pass

    def send(self, char_cmd):
        if self.connected and self.hub:
            data = bytearray(char_cmd, 'utf-8')
            asyncio.run_coroutine_threadsafe(self.hub.write(data), self.loop)

    def disconnect(self):
        if self.hub:
            self.connected = False
            asyncio.run_coroutine_threadsafe(self._disconnect_task(), self.loop)

    async def _disconnect_task(self):
        try:
            await self.hub.disconnect()
        except Exception:
            pass
        finally:
            self.hub = None

    def close(self):
        self._closing = True
        self.disconnect()
        try:
            self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception:
            pass


# 3. INTERFAZ GRÁFICA

class App:
    # Colores del tema
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

        # - HEADER -
        header = tk.Frame(root, bg=self.BG_HEADER, pady=15)
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

        # - BOTÓN CONEXIÓN -
        self.btn_connect = tk.Button(
            root, text="⚡ CONECTAR ROBOT",
            font=("Segoe UI", 12, "bold"),
            bg=self.SUCCESS, fg=self.BG_DARK,
            activebackground="#00b359", activeforeground=self.TEXT,
            cursor="hand2", relief="flat", height=2,
            command=self.do_connect
        )
        self.btn_connect.pack(fill="x", padx=25, pady=15)

        # - PANELES DE CONTROL -
        self.controls_frame = tk.Frame(root, bg=self.BG_DARK)
        self.controls_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Guardar referencias a los botones para feedback visual
        self.buttons = {}

        # Motor configs: (titulo, icono, tecla1, texto1, cmd1_press, cmd1_release,
        #                                tecla2, texto2, cmd2_press, cmd2_release, color)
        motors = [
            ("Brazo Principal", "Motor B", "W", "SUBIR", "w", "e", "S", "BAJAR", "s", "e", "#3498db"),
            ("Base Giratoria", "Motor A", "A", "HORARIO", "a", "q", "D", "ANTI-HORARIO", "d", "q", "#e67e22"),
            ("Pinza", "Motor C", "O", "ABRIR", "o", "z", "C", "CERRAR", "c", "z", "#2ecc71"),
            ("Elevador Muñeca", "Motor E", "I", "SUBIR", "i", "m", "K", "BAJAR", "k", "m", "#9b59b6"),
        ]

        for motor in motors:
            self.crear_panel(*motor)

        # - FOOTER con atajos -
        footer = tk.Frame(root, bg=self.BG_PANEL, pady=8)
        footer.pack(fill="x", side="bottom")
        tk.Label(
            footer,
            text="💡 Usa el teclado: W/S (brazo) · A/D (base) · O/C (pinza) · I/K (elevador)",
            font=("Segoe UI", 9), fg=self.TEXT_DIM, bg=self.BG_PANEL
        ).pack()

        # - BINDINGS DE TECLADO -
        self.setup_keyboard()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def crear_panel(self, titulo, subtitulo, key1, txt1, cmd1_p, cmd1_r, key2, txt2, cmd2_p, cmd2_r, color):
        frame = tk.Frame(self.controls_frame, bg=self.BG_PANEL, pady=10, padx=10)
        frame.pack(fill="x", pady=6)

        # Header del panel
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

        # Botones
        btn_frame = tk.Frame(frame, bg=self.BG_PANEL)
        btn_frame.pack(fill="x")

        btn1 = tk.Button(
            btn_frame, text=f"[{key1}] {txt1}",
            bg=color, fg="white",
            activebackground=self._darken(color), activeforeground="white",
            font=("Segoe UI", 10, "bold"), height=2,
            relief="flat", cursor="hand2"
        )
        btn1.pack(side="left", expand=True, fill="x", padx=(0, 5))
        btn1.bind('<ButtonPress-1>', lambda e: self._on_press(cmd1_p, btn1, color))
        btn1.bind('<ButtonRelease-1>', lambda e: self._on_release(cmd1_r, btn1, color))

        btn2 = tk.Button(
            btn_frame, text=f"[{key2}] {txt2}",
            bg=color, fg="white",
            activebackground=self._darken(color), activeforeground="white",
            font=("Segoe UI", 10, "bold"), height=2,
            relief="flat", cursor="hand2"
        )
        btn2.pack(side="right", expand=True, fill="x", padx=(5, 0))
        btn2.bind('<ButtonPress-1>', lambda e: self._on_press(cmd2_p, btn2, color))
        btn2.bind('<ButtonRelease-1>', lambda e: self._on_release(cmd2_r, btn2, color))

        # Guardar para control por teclado
        self.buttons[key1.lower()] = (btn1, cmd1_p, cmd1_r, color)
        self.buttons[key2.lower()] = (btn2, cmd2_p, cmd2_r, color)

    def _darken(self, hex_color, factor=0.7):
        """Oscurece un color hex para el estado activo."""
        hex_color = hex_color.lstrip('#')
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _on_press(self, cmd, btn, original_color):
        self.robot.send(cmd)
        btn.config(bg=self._darken(original_color, 0.6))

    def _on_release(self, cmd, btn, original_color):
        self.robot.send(cmd)
        btn.config(bg=original_color)

    def setup_keyboard(self):
        """Configura control por teclado (mantener presionado = mover)."""
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
        messagebox.showinfo("Éxito", "Robot conectado \nEl programa fue inyectado correctamente.\n\nUsa los botones o el teclado para controlar.")

    def on_error(self, err_msg):
        self.lbl_status.config(text="🔴 ERROR DE CONEXIÓN", fg=self.ACCENT)
        self.btn_connect.config(state="normal", text="⚡ CONECTAR ROBOT", bg=self.SUCCESS)
        messagebox.showerror("Error", f"Fallo al conectar:\n{err_msg}")

    def on_close(self):
        self.robot.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)

    root.mainloop()
