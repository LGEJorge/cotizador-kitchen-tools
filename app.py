from flask import Flask, request, send_file, render_template, render_template_string, jsonify
import base64
import os
from datetime import datetime, timedelta
import pandas as pd
from weasyprint import HTML
import re
import json
import requests

app = Flask(__name__)

EXCEL_PATH = "productos.xlsx"
IMG_FOLDER = "static/img"
LOGO_PATH = "logo_kitchen.png"
PARAMS_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "parametros.json")

#COLOCAR ESTO EN UN .ENV PARA MAYOR SEGURIDAD
URL_DUX = "https://erp.duxsoftware.com.ar/WSERP/rest/services/items/"
HEADERS = {
    "accept": "application/json",
    "authorization": "7nuVD4L4GUJ4nXUv1ZzsUMiU3wJtfeymStJfxdjF93IwamscMsVqFELIBeCqJBel"
}
PRODUCTOS_FILE = "productos.json"
productos_cache = {}  # Diccionario en memoria

#------------------------------------------

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
        
        if response.status_code != 200:
            print(f"❌ Error al consultar API (código {response.status_code})")
            break

        data = response.json()
        
        if not data:  # fin de la lista
            break

        for item in data:
            todos.append({
                "codigo": str(item.get("codigo")).strip(),
                "nombre": item.get("descripcion", ""),
                "precio": float(item.get("precioVentaConIVA", 0))
            })

        offset += limit

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

def buscar_imagen_base64(codigo):
    extensiones = [".jpg", ".png"]
    for ext in extensiones:
        ruta = os.path.join(IMG_FOLDER, f"{codigo}{ext}")
        if os.path.exists(ruta):
            with open(ruta, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    return None

def formatear_precio(valor):
    return f"{int(round(valor)):,}".replace(",", ".")

def formatear_cuota(total, cuotas):
    cuota = total / cuotas
    total_formateado = f"{int(round(total)):,}".replace(",", ".")
    cuota_formateada = f"{int(round(cuota)):,}".replace(",", ".")
    return f"${total_formateado} ({cuotas} x ${cuota_formateada})"

def cargar_parametros():
    if os.path.exists(PARAMS_FILE):
        with open(PARAMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"formas_pago": [], "marketing_fee": 0.0}

def guardar_parametros(data):
    print(f"💾 Guardando parámetros en: {PARAMS_FILE}")
    with open(PARAMS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.route("/cotizar", methods=["POST"])
def cotizar():
    codigos = request.json.get("codigos", [])
    cliente = request.json.get("cliente", "Kitchen Tools")
    formas_pago = request.json.get("formas_pago", {})
    marketing_fee = float(request.json.get("marketing_fee", 0.0))

    fecha = datetime.now()
    vencimiento_str = request.json.get("vencimiento")
    vencimiento = datetime.strptime(vencimiento_str, "%Y-%m-%d") if vencimiento_str else (fecha + timedelta(days=1))

    productos = []
    for codigo in codigos:
        prod = obtener_datos_producto(codigo)
        if prod:
            productos.append(prod)

    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("utf-8")

    for p in productos:
        precios = []
        for clave, info in formas_pago.items():
            label = info["label"]
            coef = float(info["coef"]) + marketing_fee
            precio_base = p["precio"]
            if coef < 0:
                total = precio_base * (1 + coef / 100)
            else:
                try:
                    total = precio_base / (1 - coef / 100)
                except ZeroDivisionError:
                    total = precio_base

            match = re.search(r"\b(\d+)\b", label)
            if match:
                cuotas = int(match.group(1))
                texto = formatear_cuota(total, cuotas)
            else:
                texto = f"${formatear_precio(total)}"

            precios.append({"label": label, "texto": texto})

        p["precios"] = precios

    html = render_template(
        "plantilla_pdf.html",
        cliente=cliente,
        fecha=fecha.strftime('%d/%m/%Y'),
        vencimiento=vencimiento.strftime('%d/%m/%Y'),
        productos=productos,
        logo_b64=logo_b64
    )

    output_path = "cotizacion_temp.pdf"
    HTML(string=html).write_pdf(output_path)
    return send_file(output_path, mimetype='application/pdf', as_attachment=True, download_name="cotizacion_kitchen_tools.pdf")


@app.route("/guardar-parametros", methods=["POST"])
def guardar_parametros_endpoint():
    data = request.json
    guardar_parametros(data)
    return jsonify({"mensaje": "Parámetros guardados correctamente"})


@app.route("/obtener-parametros", methods=["GET"])
def obtener_parametros_endpoint():
    return jsonify(cargar_parametros())


@app.route("/vista-previa")
def vista_previa():
    codigos = ["123", "456"]  # Ejemplo de códigos
    cliente = "Ejemplo Cliente"
    formas_pago = {"Efectivo": {"label": "Efectivo", "coef": -10}, "Tarjeta 3 cuotas": {"label": "Tarjeta 3 cuotas", "coef": 7.5}}
    marketing_fee = 2.0

    fecha = datetime.now()
    vencimiento = fecha + timedelta(days=1)

    productos = []
    for codigo in codigos:
        prod = obtener_datos_producto(codigo)
        if prod:
            productos.append(prod)

    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("utf-8")

    for p in productos:
        precios = []
        for clave, info in formas_pago.items():
            label = info["label"]
            coef = float(info["coef"]) + marketing_fee
            precio_base = p["precio"]
            if coef < 0:
                total = precio_base * (1 + coef / 100)
            else:
                try:
                    total = precio_base / (1 - coef / 100)
                except ZeroDivisionError:
                    total = precio_base

            match = re.search(r"\b(\d+)\b", label)
            if match:
                cuotas = int(match.group(1))
                texto = formatear_cuota(total, cuotas)
            else:
                texto = f"${formatear_precio(total)}"

            precios.append({"label": label, "texto": texto})

        p["precios"] = precios

    html = render_template(
        "plantilla_pdf.html",
        cliente=cliente,
        fecha=fecha.strftime('%d/%m/%Y'),
        vencimiento=vencimiento.strftime('%d/%m/%Y'),
        productos=productos,
        logo_b64=logo_b64
    )

    return html


@app.route("/")
def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return render_template_string(f.read())


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
