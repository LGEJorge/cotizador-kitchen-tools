import os
import subprocess
from datetime import datetime

# Ruta principal del proyecto
PROJECT_DIR = "C:/Users/Jorge/Desktop/CotizadorKitchenTools"
IMG_FOLDER = os.path.join(PROJECT_DIR, "static/img")
ARCHIVOS_CLAVE = ["app.py", "index.html", "productos.xlsx"]

# Cambiar al directorio del proyecto
os.chdir(PROJECT_DIR)

def ejecutar_comando(cmd):
    try:
        subprocess.run(cmd, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar el comando: {cmd}")
        print(e)

def hubo_cambios():
    resultado = subprocess.run("git status --porcelain", capture_output=True, text=True, shell=True)
    return bool(resultado.stdout.strip())

def sincronizar_con_git():
    print("📡 Verificando cambios...")

    # Agrega imágenes si hay cambios
    ejecutar_comando(f'git add static/img')

    # Agrega archivos clave
    for archivo in ARCHIVOS_CLAVE:
        ruta = os.path.join(PROJECT_DIR, archivo)
        if os.path.exists(ruta):
            ejecutar_comando(f'git add {archivo}')

    if not hubo_cambios():
        print("✅ No hay cambios nuevos para sincronizar.")
        return

    # Commit con fecha y hora
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensaje = f"🔄 Actualización automática {ahora}"
    ejecutar_comando(f'git commit -m "{mensaje}"')

    # Push al repositorio
    ejecutar_comando('git push origin main')
    print("✅ Sincronización completada con éxito.")

if __name__ == "__main__":
    sincronizar_con_git()
