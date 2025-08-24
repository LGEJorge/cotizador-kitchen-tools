import redis
import json
import os

PARAMS_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "parametros.json")

r = redis.Redis(
    host='redis-18037.crce181.sa-east-1-2.ec2.redns.redis-cloud.com',
    port=18037,
    decode_responses=True,
    username="admin",
    password="KitchenTools2025*",
    db="0"
)

data = {
    "formas_pago": [
        {"label": "Transferencia", "coef": 0},
        {"label": "Efectivo", "coef": -10},
        {"label": "Tarjeta 2 Cuotas", "coef": 14.27},
        {"label": "Tarjeta 3 Cuotas", "coef": 17.17},
        {"label": "Tarjeta 6 Cuotas", "coef": 24.31},
        {"label": "Tarjeta 9 Cuotas", "coef": 31.93},
        {"label": "Tarjeta 12 Cuotas", "coef": 39.31},
        {"label": "Bco. Galicia 3 y 6 Cuotas", "coef": 7}
    ],
    "marketing_fee": 0
}

parametros = json.loads(r.get('parametros'))

def guardar_parametros(data):
    print(f"💾 Guardando parámetros en la nube")
    r.set('parametros', json.dumps(data))

def cargar_parametros():
    parametros = r.get('parametros')
    if parametros:
        return json.loads(parametros)
    return {"formas_pago": [], "marketing_fee": 0.0}

print(f"{r.get('parametros')}")