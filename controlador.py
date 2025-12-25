# Controlador de conexión BLE para el Hub LEGO SPIKE Prime
# Maneja la comunicación Bluetooth y transferencia de programas

import asyncio
import threading
import tempfile
import os
from pybricksdev.ble import find_device
from pybricksdev.connections.pybricks import PybricksHubBLE
from Servidor import HUB_PROGRAM


# Tiempos de espera para las operaciones BLE
FIND_DEVICE_TIMEOUT = 20
CONNECT_TIMEOUT = 20
RUN_PROGRAM_TIMEOUT = 30
HUB_NAME = "PY-SC"


class RobotController:
    """Controla la conexión y comunicación con el Hub LEGO."""
    
    def __init__(self):
        self.hub = None
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.connected = False
        self._closing = False

    def _run_loop(self):
        """Ejecuta el loop de asyncio en un hilo separado."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def connect(self, on_success, on_error):
        """Inicia la conexión al Hub en segundo plano."""
        if self._closing:
            on_error("El controlador se está cerrando.")
            return
        asyncio.run_coroutine_threadsafe(
            self._connect_task(on_success, on_error), 
            self.loop
        )

    async def _connect_task(self, on_success, on_error):
        """Busca el Hub por BLE, se conecta y transfiere el programa."""
        temp_path = None
        try:
            print("Buscando robot...")
            device = await find_device(name=HUB_NAME, timeout=FIND_DEVICE_TIMEOUT)
            if not device:
                on_error("No se encontró el Hub. Verifica que esté encendido.")
                return

            print(f"Encontrado: {device.name}")
            self.hub = PybricksHubBLE(device)
            await asyncio.wait_for(self.hub.connect(), timeout=CONNECT_TIMEOUT)
            
            print("Transfiriendo programa al Hub...")
            
            # Crea archivo temporal y lo transfiere al Hub
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, encoding='utf-8'
            ) as tf:
                tf.write(HUB_PROGRAM)
                temp_path = tf.name
            
            await asyncio.wait_for(
                self.hub.run(temp_path, wait=False), 
                timeout=RUN_PROGRAM_TIMEOUT
            )
            
            self.connected = True
            print("Conexión establecida. Control activado.")
            on_success()
            
        except asyncio.TimeoutError:
            on_error("Tiempo de espera agotado. Verifica que el Hub esté en modo Pybricks.")

        except Exception as e:
            print(f"Error de conexión: {e}")
            on_error(str(e))
        
        finally:
            # Limpia el archivo temporal
            if temp_path and os.path.exists(temp_path):
                try: 
                    os.unlink(temp_path)
                except: 
                    pass

    def send(self, command):
        """Envía un comando al Hub."""
        if self.connected and self.hub:
            data = bytearray(command, 'utf-8')
            asyncio.run_coroutine_threadsafe(self.hub.write(data), self.loop)

    def disconnect(self):
        """Cierra la conexión BLE con el Hub."""
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
        """Cierra el controlador."""
        self._closing = True
        self.disconnect()
        try:
            self.loop.call_soon_threadsafe(self.loop.stop)
        except Exception:
            pass
