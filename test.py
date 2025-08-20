import requests
import os
import json
import time

# COLOCAR ESTO EN UN .ENV PARA MAYOR SEGURIDAD
URL_DUX = "https://erp.duxsoftware.com.ar/WSERP/rest/services/items/"
HEADERS = {
    "accept": "application/json",
    "authorization": "7nuVD4L4GUJ4nXUv1ZzsUMiU3wJtfeymStJfxdjF93IwamscMsVqFELIBeCqJBel"
}
PRODUCTOS_FILE = "productos.json"
productos_cache = {}  # Diccionario en memoria

def actualizarListaProductos():
    print("📡 Descargando lista completa de productos desde Dux...")
    todos = []
    offset = 0
    limit = 50

    while True:
        response = requests.get(
            f"{URL_DUX}?offset={offset}&limit={limit}",
            headers=HEADERS
        )
        
        if response.status_code == 429:
            print("⏳ Rate limit alcanzado, esperando 2 segundos...")
            time.sleep(2)
            continue  # reintenta la misma página


        if response.status_code != 200:
            print(f"❌ Error al consultar API (código {response.status_code})")
            break

        data = response.json()
        
        results = data.get("results", [])
        if not results:  # fin de la lista
            break

        for item in results:
            # Buscar precio dentro de la lista de precios
            precio = None
            for precio_info in item.get("precios", []):
                if precio_info.get("nombre") == "TIENDA NUBE":  # 👈 elegí la lista de precios que te sirva
                    precio = float(precio_info.get("precio", 0))
                    break
            if precio is None:
                # fallback: tomamos el primero o 0
                precio = float(item.get("precios", [{}])[0].get("precio", 0))

            todos.append({
                "codigo": str(item.get("cod_item")).strip(),
                "nombre": item.get("item", ""),
                "precio": precio,
                "imagen_url": item.get("imagen_url", None)
            })

        offset += limit
        time.sleep(0.2)  # espera 200ms entre páginas

    # Guardar en archivo
    with open(PRODUCTOS_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    print(f"✅ Lista de productos actualizada. Total: {len(todos)}")

def cargar_productos():
    global productos_cache
    if not os.path.exists(PRODUCTOS_FILE):
        actualizarListaProductos()
    with open(PRODUCTOS_FILE, "r", encoding="utf-8") as f:
        productos_cache = {p["codigo"]: p for p in json.load(f)}
    print(f"📦 Productos cargados en memoria: {len(productos_cache)}")

def obtener_datos_producto(codigo):
    return productos_cache.get(str(codigo))

# Ejecutar prueba
actualizarListaProductos()
cargar_productos()

producto = obtener_datos_producto(1141801)

if producto:
    print("✅ Producto encontrado:", producto)
else:
    print("❌ Producto no encontrado")
