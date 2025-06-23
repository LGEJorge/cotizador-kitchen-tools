import os
import shutil
from filecmp import cmp

drive_folder = r"G:\.shortcut-targets-by-id\1-R_zY7rBbem5DmHclokxLZF-wYsdvjep\IMAGENES SUBIDAS"  # ← REEMPLAZAR con la ruta real de tu carpeta de Drive
dest_folder = r"C:\Users\Jorge\Desktop\CotizadorKitchenTools\static\img"

extensiones_validas = {".jpg", ".png"}
copiados = 0
reemplazados = 0
eliminados = 0

# Obtener archivos fuente
archivos_drive = {
    archivo: os.path.join(drive_folder, archivo)
    for archivo in os.listdir(drive_folder)
    if os.path.splitext(archivo)[1].lower() in extensiones_validas
}

# Obtener archivos de destino
archivos_destino = {
    archivo: os.path.join(dest_folder, archivo)
    for archivo in os.listdir(dest_folder)
    if os.path.splitext(archivo)[1].lower() in extensiones_validas
}

# Copiar o reemplazar archivos nuevos/modificados
for nombre, ruta_origen in archivos_drive.items():
    ruta_destino = os.path.join(dest_folder, nombre)
    if not os.path.exists(ruta_destino):
        shutil.copy2(ruta_origen, ruta_destino)
        copiados += 1
    elif not cmp(ruta_origen, ruta_destino, shallow=False):
        shutil.copy2(ruta_origen, ruta_destino)
        reemplazados += 1

# Eliminar archivos que ya no están en Drive
for nombre in archivos_destino:
    if nombre not in archivos_drive:
        os.remove(archivos_destino[nombre])
        eliminados += 1

# Mostrar resumen
print("✅ Sincronización completada.")
print(f"🆕 Imágenes nuevas copiadas: {copiados}")
print(f"🔁 Imágenes actualizadas (reemplazadas): {reemplazados}")
print(f"🗑️ Imágenes eliminadas: {eliminados}")
