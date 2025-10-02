from googleapiclient.discovery import build
from products.redis_service import cargar_token

def crear_drive_service():
    credentials = cargar_token()
    return build("drive", "v3", credentials=credentials)

def obtener_imagen_base64_por_sku(service, sku):
    carpeta_id = "1NMgqDd8fzBQV1ShiUWl-waSxxPvsUAaM"
    query = f"name = '{sku}.jpg' and '{carpeta_id}' in parents and mimeType contains 'image/' and trashed = false"
    resultados = service.files().list(q=query, fields="files(id)").execute()
    archivos = resultados.get("files", [])

    if archivos:
        file_id = archivos[0]["id"]
        request = service.files().get_media(fileId=file_id)

        from io import BytesIO
        from googleapiclient.http import MediaIoBaseDownload
        import base64

        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        imagen_b64 = base64.b64encode(fh.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{imagen_b64}"

    return None