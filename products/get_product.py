from products.products_loader import get_producto_por_codigo

def obtener_datos_producto(codigo):
    producto = get_producto_por_codigo(codigo)
    if producto:
        return producto