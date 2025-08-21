from products.products_loader import get_producto_por_codigo

def obtener_datos_producto(codigo):
    producto = get_producto_por_codigo(codigo)
    if producto:
        print(f"Estoy en obtener datos y el precio es {producto["precio"]}")
        return producto