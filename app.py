from flask import Flask, request, redirect, send_file, render_template, render_template_string, jsonify, url_for

#Variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Importo librería de Gooogle Auth
from google_auth_oauthlib.flow import Flow

from products.products_loader import cargar_productos, get_producto_por_codigo
from products.scheduler import iniciar_scheduler
from utils.price_formater import formatear_precio
from utils.gmail_service import enviar_cotizacion
from utils.perfit_service import cargar_contacto_prefit
from products.redis_service import guardar_parametros, cargar_parametros, guardar_token
from products.drive_service import crear_drive_service, obtener_url_imagen_por_sku

from config import AppState

from datetime import datetime, timedelta
from weasyprint import HTML

import json
import base64
import os
import re

app = Flask(__name__)

IMG_FOLDER = "static/img"
LOGO_PATH = "logo_kitchen.png"
PARAMS_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "parametros.json")

# Le aviso al OAuth que estoy en entorno de desarrollo
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

def formatear_cuota(total, cuotas):
    cuota = total / cuotas
    total_formateado = f"{int(round(total)):,}".replace(",", ".")
    cuota_formateada = f"{int(round(cuota)):,}".replace(",", ".")
    return f"${total_formateado} ({cuotas} x ${cuota_formateada})"

flow = Flow.from_client_config(
    {
        "web": {
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [os.environ["REDIRECT_URI"]]
        }
    },
    scopes=["https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/drive.readonly"
    ],
    redirect_uri=os.environ["REDIRECT_URI"]
)

@app.route('/authorize')
def authorize():
    authorization_url, state = flow.authorization_url(
    access_type='offline',
    include_granted_scopes='true',
    prompt='consent'
    )
    
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    guardar_token(json.loads(credentials.to_json()))
    return redirect(url_for('home', autorizado='true'))

@app.route("/cotizar", methods=["POST"])
def cotizar():
    with AppState.update_lock:
        if AppState.is_updating_products:
            return jsonify({"mensaje": "⏳ Cotización en pausa por actualización de productos"}), 409
        
        codigos = request.json.get("codigos", [])
        cliente = request.json.get("cliente", "Kitchen Tools")
        mail = request.json.get("mail", "")
        telefono = request.json.get("telefono", "")
        rubro = request.json.get("rubro", "")

        formas_pago = request.json.get("formas_pago", {})
        marketing_fee = float(request.json.get("marketing_fee", 0.0))

        fecha = datetime.now()
        vencimiento_str = request.json.get("vencimiento")
        vencimiento = datetime.strptime(vencimiento_str, "%Y-%m-%d") if vencimiento_str else (fecha + timedelta(days=1))

        productos = []

        for codigo in codigos:
            prod = get_producto_por_codigo(codigo)

            if prod:
                productos.append(prod)

    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("utf-8")

    try:
        drive_service = crear_drive_service()
    except Exception as e:
        print(f"{e}")
        
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
        p["imagen_url"] = obtener_url_imagen_por_sku(drive_service, p["codigo"])
        # p["imagen_b64"] = buscar_imagen_base64(p["codigo"])

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

    if mail != "":
        with open(output_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()

            asunto = "Tu presupuesto Kitchen Tools"
            cuerpo = f"""Hola {cliente},
            Adjunto el presupuesto solicitado. Cualquier duda, estoy a disposición.

            Saludos,
            Kitchen Tools"""

            try:
                enviar_cotizacion(mail, asunto, cuerpo, pdf_bytes, "cotizacion_kitchen_tools.pdf")
                print("✅ Correo enviado con éxito.")
            except Exception as e:
                print(f"❌ Error al enviar correo: {e}")

    if mail != "" or telefono != "":
        cargar_contacto_prefit(mail, cliente, telefono, rubro)

    return send_file(output_path, mimetype='application/pdf', as_attachment=True, download_name=f"cotizacion_{cliente}_kitchen_tools.pdf")

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
        AppState.is_updating_products = True # 🚩 marco que estoy actualizando

    try:
        cargar_productos()
        return jsonify({"mensaje": "✅ Lista actualizada correctamente"})
    finally:
        AppState.is_updating_products = False # ✅ Libero el flag porque ya actualice

@app.route("/")
def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return render_template_string(f.read())

if __name__ == "__main__":
    cargar_productos()
    iniciar_scheduler()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)