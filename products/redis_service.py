from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

import redis
import json
import os

PARAMS_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "parametros.json")
EXPIRACION_TOKEN = 30 * 24 * 60 * 60  # 30 días
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive.readonly"
]

r = redis.Redis(
    host='redis-18037.crce181.sa-east-1-2.ec2.redns.redis-cloud.com',
    port=18037,
    decode_responses=True,
    username="admin",
    password= os.environ.get("REDIS_PASSWORD"),
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

def guardar_token(data):
    print("💾 Guardando token en Redis")
    r.setex('token', EXPIRACION_TOKEN, json.dumps(data))

def cargar_token():
    token_json = r.get('token')

    if not token_json:
        return None

    credentials = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)

    if credentials.expired and credentials.refresh_token:
        print("🔄 Token vencido, refrescando...")
        credentials.refresh(Request())
        guardar_token(json.loads(credentials.to_json()))
        print("✅ Token actualizado y guardado")

    if not credentials.expired:
        print("✅ Token NO vencido...")

    return credentials if credentials.valid else None

def guardar_parametros(data):
    print(f"💾 Guardando parámetros en la nube")
    r.set('parametros', json.dumps(data))

def cargar_parametros():
    parametros = r.get('parametros')
    if parametros:
        return json.loads(parametros)
    return {"formas_pago": [], "marketing_fee": 0.0}