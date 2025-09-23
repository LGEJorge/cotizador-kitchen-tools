import requests, time, json
from config import URL_DUX, HEADERS, PRODUCTOS_FILE

def actualizar_lista_productos():
    print("📡 Descargando lista completa de productos desde Dux...")
    todos = []
    offset = 0
    limit = 50
    pagina = 1
    intentos_fallidos = 0

    while True:
        print(f"🔄 Página {pagina} | Offset: {offset}")
        response = requests.get(f"{URL_DUX}?offset={offset}&limit={limit}", headers=HEADERS)

        # Sobrecarga de peticiones
        if response.status_code == 429:
            print(f"⏳ Rate limit alcanzado, esperando 5 segundos... Productos cargados hasta el momento: {offset}")
            time.sleep(5)
            continue  # reintenta la misma página

        # Error inesperado
        if response.status_code != 200:
            print(f"❌ Error al consultar API (código {response.status_code})")
            intentos_fallidos += 1
            if intentos_fallidos >= 3:
                print("🚫 Demasiados errores consecutivos. Abortando.")
                break
            time.sleep(2)
            continue  # reintenta la misma página

        data = response.json()
        results = data.get("results", [])

        # Página vacía inesperada
        if not results:
            print("⚠️ Página vacía recibida. Reintentando...")
            intentos_fallidos += 1
            if intentos_fallidos >= 3:
                print("🚫 Demasiadas páginas vacías consecutivas. Fin de la lista.")
                break
            time.sleep(1)
            continue  # reintenta la misma página

        intentos_fallidos = 0  # reinicia contador si la página fue válida

        for item in results:
            precio = 0.0
            for precio_info in item.get("precios", []):
                nombre_lista = precio_info.get("nombre", "").strip().upper()
                if nombre_lista == "KT GASTRO":
                    try:
                        precio = float(precio_info.get("precio", 0))
                    except (ValueError, TypeError):
                        precio = 0.0
                    break

            todos.append({
                "codigo": str(item.get("cod_item")).strip(),
                "nombre": item.get("item", ""),
                "precio": precio,
                "imagen_url": item.get("imagen_url", None)
            })

        offset += limit
        pagina += 1
        time.sleep(0.2)

    with open(PRODUCTOS_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    print(f"✅ Lista de productos actualizada. Total: {len(todos)}")