from threading import Lock
class AppState:
    is_products_list_loaded = False
    is_updating_products = False
    update_lock = Lock()

URL_DUX = "https://erp.duxsoftware.com.ar/WSERP/rest/services/items"
HEADERS = {
    "accept": "application/json",
    "authorization": "7nuVD4L4GUJ4nXUv1ZzsUMiU3wJtfeymStJfxdjF93IwamscMsVqFELIBeCqJBel"
}
PRODUCTOS_FILE = "productos.json"
IMG_FOLDER = "static/img"
LOGO_PATH = "logo_kitchen.png"

