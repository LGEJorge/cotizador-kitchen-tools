from flask import Flask, request, send_file, render_template_string
import base64
import os
from datetime import datetime, timedelta
import pandas as pd
from weasyprint import HTML
import re

app = Flask(__name__)

EXCEL_PATH = "productos.xlsx"
IMG_FOLDER = "static/img"
LOGO_PATH = "logo_kitchen.png"
MARKETING_FEE = 0.02

def buscar_imagen_base64(codigo):
    extensiones = [".jpg", ".png"]
    for ext in extensiones:
        ruta = os.path.join(IMG_FOLDER, f"{codigo}{ext}")
        if os.path.exists(ruta):
            with open(ruta, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    return None

def obtener_datos_producto(codigo):
    try:
        df = pd.read_excel(EXCEL_PATH, header=2)
        df['Cod Producto'] = df['Cod Producto'].astype(str).str.strip()
        codigo = str(codigo).strip()
        fila_filtrada = df[df['Cod Producto'] == codigo]

        if fila_filtrada.empty:
            print(f"❌ No se encontró el código '{codigo}' en el Excel.")
            return None

        fila = fila_filtrada.iloc[0]
        return {
            "codigo": codigo,
            "nombre": fila['Producto'],
            "precio": float(fila['Precio De Venta Con Iva']),
            "imagen_b64": buscar_imagen_base64(codigo)
        }
    except Exception as e:
        print("⚠️ Error buscando producto:", e)
        return None

def formatear_precio(valor):
    return f"{int(round(valor)):,}".replace(",", ".")

def formatear_cuota(total, cuotas):
    cuota = total / cuotas
    total_formateado = f"{int(round(total)):,}".replace(",", ".")
    cuota_formateada = f"{int(round(cuota)):,}".replace(",", ".")
    return f"${total_formateado} ({cuotas} x ${cuota_formateada})"

@app.route("/cotizar", methods=["POST"])
def cotizar():
    codigos = request.json.get("codigos", [])
    cliente = request.json.get("cliente", "Kitchen Tools")
    formas_pago = request.json.get("formas_pago", {})
    marketing_fee = float(request.json.get("marketing_fee", MARKETING_FEE))

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

    filas_html = ""
    for p in productos:
        filas_html += f'''<table style="width:100%; border:1px solid #ccc; border-collapse:collapse; margin-bottom:15px;">
            <tr>
                <td style="width:170px; padding:10px;">
                    <img src="data:image/jpeg;base64,{p['imagen_b64']}" style="width:160px; height:auto; border-radius:5px;">
                </td>
                <td style="padding:10px; vertical-align:top;">
                    <h2 style="margin:0 0 5px 0; color:#0d3a5e; font-size:17px;">{p['nombre']}</h2>
                    <p style="margin:0 0 10px 0;"><em>Código: {p['codigo']}</em></p>
                    <ul style="margin-top:10px; font-size:17px; line-height:2.8em;">
        '''

        for clave, info in formas_pago.items():
            label = info["label"]
            coef = float(info["coef"])
            if "cuotas" in label.lower() or "cuota" in label.lower():
                coef += marketing_fee

            total = p['precio'] * (1 + (coef/100))

            match = re.search(r"\\b(\\d+)\\b", label)
            if match:
                cuotas = int(match.group(1))
                filas_html += f"<li><strong>{label}:</strong> {formatear_cuota(total, cuotas)}</li>"
            else:
                filas_html += f"<li><strong>{label}:</strong> ${formatear_precio(total)}</li>"

        filas_html += "</ul></td></tr></table>"

    html = f'''
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:Arial; margin:10px;">
        <div style="display:flex; align-items:center;">
            <img src="data:image/png;base64,{logo_b64}" style="height:50px; margin-right:10px;">
            <h1 style="flex:1; text-align:center;">Cotización - {cliente}</h1>
        </div>
        <p style="text-align:center;">
            Fecha: {fecha.strftime('%d/%m/%Y')} |
            <span style="color:red;">Válido hasta: {vencimiento.strftime('%d/%m/%Y')}</span>
        </p>
        {filas_html}
        <p style="font-size:10px; font-style:italic;">Precios sujetos a modificación. Consultar condiciones vigentes.</p>
        <p style="text-align:center; font-size:11px;">WhatsApp: +54 9 11 3816-8648<br>Instagram: @kitchentools.ig</p>
    </body>
    </html>
    '''

    output_path = "cotizacion_temp.pdf"
    HTML(string=html).write_pdf(output_path)
    return send_file(output_path, mimetype='application/pdf', as_attachment=True, download_name="cotizacion_kitchen_tools.pdf")

@app.route("/")
def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return render_template_string(f.read())

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
