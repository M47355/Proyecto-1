# Programa MicroPython para el Hub LEGO SPIKE Prime
# Este archivo contiene el código que se transfiere al Hub vía BLE

HUB_PROGRAM = """
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Color
from pybricks.tools import wait
from usys import stdin
import uselect

# Inicializa el Hub y enciende la luz en rojo mientras carga
hub = PrimeHub()
hub.light.on(Color.RED)

# Intenta conectar cada motor, si no está conectado queda en None
try: m_base = Motor(Port.A)
except: m_base = None

try: m_brazo = Motor(Port.B)
except: m_brazo = None

try: m_pinza = Motor(Port.C)
except: m_pinza = None

try: m_elev = Motor(Port.E)
except: m_elev = None

# Luz verde = listo para recibir comandos
hub.light.on(Color.GREEN)

# Bucle principal: espera comandos del PC
while True:
    if uselect.select([stdin], [], [], 0)[0]:
        cmd = stdin.read(1)
        
        # Motor A - Base giratoria
        if cmd == "a" and m_base: m_base.run(-200)
        elif cmd == "d" and m_base: m_base.run(200)
        elif cmd == "q" and m_base: m_base.stop()
            
        # Motor B - Brazo principal
        elif cmd == "w" and m_brazo: m_brazo.run(-200)
        elif cmd == "s" and m_brazo: m_brazo.run(200)
        elif cmd == "e" and m_brazo: m_brazo.hold()
            
        # Motor C - Pinza
        elif cmd == "o" and m_pinza: m_pinza.run(-100)
        elif cmd == "c" and m_pinza: m_pinza.run(100)
        elif cmd == "z" and m_pinza: m_pinza.stop()
            
        # Motor E - Elevador de muñeca
        elif cmd == "i" and m_elev: m_elev.run(100)
        elif cmd == "k" and m_elev: m_elev.run(-100)
        elif cmd == "m" and m_elev: m_elev.hold()
        
    wait(10)
"""
