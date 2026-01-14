import json
import os
from config import PRODUCTOS_FILE
from config import AppState
from products.updater import actualizar_lista_productos

products_list = {}

def get_producto_por_codigo(codigo):
    return products_list.get(str(codigo))

def cargar_productos(force_update=False):
    global products_list
    AppState.is_products_list_loaded = False # 🚩 Marco que estoy actualizando

    if force_update or not os.path.exists(PRODUCTOS_FILE):
        print("⚡ Iniciando actualización de productos...")
        actualizar_lista_productos()
    else:
        print("⚡ Usando archivo de productos en caché.")

    if os.path.exists(PRODUCTOS_FILE):
        with open(PRODUCTOS_FILE, "r", encoding="utf-8") as f:
            products_list = {p["codigo"]: p for p in json.load(f)} #De products_list es de donde saco los datos de los precios
    
    AppState.is_products_list_loaded = True #Ya se cargó la lista lo vuelvo a colocar en True
    print(f"📦 Productos cargados en memoria: {len(products_list)}")