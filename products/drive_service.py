from googleapiclient.discovery import build
from products.redis_service import cargar_token

def crear_drive_service():
    credentials = cargar_token()
    return build("drive", "v3", credentials=credentials)

def obtener_url_imagen_por_sku(service, sku):
    query = f"name = '{sku}.jpg' and mimeType contains 'image/' and trashed = false"
    resultados = service.files().list(q=query, fields="files(id)").execute()
    archivos = resultados.get("files", [])
    
    if archivos:
        file_id = archivos[0]["id"]
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    
    return None