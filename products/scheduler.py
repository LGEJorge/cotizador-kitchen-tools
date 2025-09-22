import time
import threading
from datetime import datetime
from products.updater import actualizar_lista_productos
from products.redis_service import cargar_token

already_updated_at_night = False

def dentro_del_horario():
    hora = datetime.now().hour
    return hora >= 21 or hora < 4

def iniciar_scheduler():
    print("🛎️ Monitorización nocturna activada...")

    def run():
        global already_updated_at_night

        while True:
            if dentro_del_horario():
                if not already_updated_at_night:
                    print("🌙 Dentro del horario nocturno")

                    # Refrescar token si es necesario (pero no bloquear si falla)
                    try:
                        cargar_token()
                        print("🔐 Token verificado (o actualizado si vencido)")
                    except Exception as e:
                        print(f"⚠️ Error al verificar token: {e}")

                    print("📦 Actualizando productos...")
                    actualizar_lista_productos()
                    already_updated_at_night = True
                else:
                    print("✅ Ya se actualizó esta noche, esperando...")
            else:
                if already_updated_at_night:
                    print("🌅 Salimos del horario nocturno, reiniciando flag")
                    already_updated_at_night = False
                else:
                    print("⏳ Fuera del horario nocturno, esperando...")

            time.sleep(3600)

    threading.Thread(target=run, daemon=True).start()