import time
import threading
from datetime import datetime
from products.updater import actualizar_lista_productos

def dentro_del_horario():
    hora = datetime.now().hour
    return hora >= 21 or hora < 4

def iniciar_scheduler():
    print("Monitorización nocturna activada...")
    def run():
        while True:
            if dentro_del_horario():
                print("🌙 Actualizando productos...")
                actualizar_lista_productos()
            else:
                print("⏳ Esperando próxima ventana...")
            time.sleep(3600)

    threading.Thread(target=run, daemon=True).start()