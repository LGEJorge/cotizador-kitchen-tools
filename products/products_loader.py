import json
from config import PRODUCTOS_FILE
from config import AppState
# from products.updater import actualizarListaProductos

products_list = {}

def get_producto_por_codigo(codigo):
    return products_list.get(str(codigo))


def cargar_productos():
    global products_list
    AppState.is_products_list_loaded = False

    # actualizarListaProductos()

    with open(PRODUCTOS_FILE, "r", encoding="utf-8") as f:
        products_list = {p["codigo"]: p for p in json.load(f)}

    print(f"{products_list[str(1141801)]["precio"]}")


    AppState.is_products_list_loaded = True
    print(f"📦 Productos cargados en memoria: {len(products_list)}")