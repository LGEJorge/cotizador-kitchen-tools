import subprocess
import os
import time

RUTA_REPO = os.path.abspath(".")
INDEX_LOCK = os.path.join(RUTA_REPO, ".git", "index.lock")

def ejecutar_comando(comando):
    try:
        resultado = subprocess.run(comando, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        return resultado.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode("utf-8")
        if "index.lock" in error_msg:
            print("⚠️ Se detectó un archivo de bloqueo .git/index.lock. Intentando eliminarlo...")
            if os.path.exists(INDEX_LOCK):
                os.remove(INDEX_LOCK)
                print("✅ Archivo index.lock eliminado.")
                print("🔁 Reintentando el comando...")
                return ejecutar_comando(comando)  # Retry
        print(f"❌ Error al ejecutar un comando de Git: {error_msg}")
        return None

def subir_a_github():
    print("🔄 Subiendo imágenes y Excel a GitHub...")
    
    ejecutar_comando("git add static/img")
    ejecutar_comando("git add productos.xlsx")
    
    fecha_hora = time.strftime("%Y-%m-%d %H:%M:%S")
    ejecutar_comando(f'git commit -m "Actualización automática - {fecha_hora}"')
    
    resultado_push = ejecutar_comando("git push origin main")
    if resultado_push:
        print("✅ Cambios subidos a GitHub correctamente.")

if __name__ == "__main__":
    subir_a_github()
