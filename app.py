from flask import Flask, request, send_file, render_template, render_template_string, jsonify


from products.products_loader import cargar_productos
from products.updater import actualizar_lista_productos
from products.scheduler import iniciar_scheduler
from utils.price_formater import formatear_precio
from products.get_product import obtener_datos_producto
from config import AppState

from datetime import datetime, timedelta
from weasyprint import HTML

import base64
import os
import re
import json
import requests

app = Flask(__name__)

IMG_FOLDER = "static/img"
LOGO_PATH = "logo_kitchen.png"
PARAMS_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "parametros.json")


def buscar_imagen_base64(codigo):
    extensiones = [".jpg", ".png"]
    for ext in extensiones:
        ruta = os.path.join(IMG_FOLDER, f"{codigo}{ext}")
        if os.path.exists(ruta):
            with open(ruta, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    return None

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
    with AppState.update_lock:
        if AppState.is_updating_products:
            return jsonify({"mensaje": "⏳ Cotización en pausa por actualización de productos"}), 409
        
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
        p["imagen_b64"] = buscar_imagen_base64(p["codigo"])

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

@app.route("/forzar-actualizacion", methods=["POST"])
def forzar_actualizacion():
    with AppState.update_lock:
        if AppState.is_updating_products:
            return jsonify({"mensaje": "⚠️ Ya se está actualizando"}), 409
        AppState.is_updating_products = True

    try:
        actualizar_lista_productos()
        AppState.is_products_list_loaded = True
        return jsonify({"mensaje": "✅ Lista actualizada correctamente"})
    finally:
        with AppState.update_lock:
            AppState.is_updating_products = False

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
    cargar_productos()
    iniciar_scheduler()
    app.run(host="0.0.0.0", debug=False)