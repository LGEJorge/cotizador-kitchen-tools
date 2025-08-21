import requests, time, json
from config import URL_DUX, HEADERS, PRODUCTOS_FILE

def actualizar_lista_productos():
    print("📡 Descargando lista completa de productos desde Dux...")
    todos = []
    offset = 0
    limit = 50

    while True:
        response = requests.get(f"{URL_DUX}?offset={offset}&limit={limit}",headers=HEADERS)

        # Sobrecarga de peticiones
        if response.status_code == 429:
            print(f"⏳ Rate limit alcanzado, esperando 5 segundos...Productos cargados hasta el momento: {offset}")
            time.sleep(5)
            continue  # reintenta la misma página

        # error
        if response.status_code != 200:
            print(f"❌ Error al consultar API (código {response.status_code})")
            break

        data = response.json()
        results = data.get("results", [])
        
        # fin de la lista
        if not results:
            print("No hay más productos")
            break

        # Buscar precio dentro de la lista de precios
        for item in results:
            precio = 0.0

            # Buscamos el precio de la lista MAQUINAS

            for precio_info in item.get("precios", []):

                # Este nombre permite que en un futuro se pueda cambiar facilmente de la lista MAQUINAS a OTRO
                nombre_lista = precio_info.get("nombre", "").strip().upper()
                if nombre_lista == "MAQUINAS":
                    try:
                        precio = float(precio_info.get("precio", 0))
                    except (ValueError, TypeError):
                        precio = 0.0
                    break  # ya lo encontramos, no seguimos buscando

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
