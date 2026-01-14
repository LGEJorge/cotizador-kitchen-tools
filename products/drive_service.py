from googleapiclient.discovery import build
from products.redis_service import cargar_token

def crear_drive_service():
    credentials = cargar_token()
    return build("drive", "v3", credentials=credentials)

def obtener_imagen_base64_por_sku(service, sku):
    carpeta_id = "1O_lJSVDiXSJ37_IgSVh5AScFhc-hBWPt"
    query = f"name = '{sku}.jpg' and '{carpeta_id}' in parents and mimeType contains 'image/' and trashed = false"
    resultados = service.files().list(q=query, fields="files(id)").execute()
    archivos = resultados.get("files", [])

    if archivos:
        file_id = archivos[0]["id"]
        request = service.files().get_media(fileId=file_id)

        from io import BytesIO
        from googleapiclient.http import MediaIoBaseDownload
        import base64
        from PIL import Image, ImageChops

        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        # Process image with PIL to crop white borders
        try:
            fh.seek(0)
            img = Image.open(fh)
            
            # Ensure RGB to avoid issues with transparency or other modes when checking for white
            img = img.convert("RGB")
            
            def recortar_imagen(im):
                bg = Image.new(im.mode, im.size, (255, 255, 255))
                diff = ImageChops.difference(im, bg)
                diff = ImageChops.add(diff, diff, 2.0, -100)
                bbox = diff.getbbox()
                if bbox:
                    return im.crop(bbox)
                return im

            img_cropped = recortar_imagen(img)
            
            # Save cropped image to buffer
            buffered = BytesIO()
            img_cropped.save(buffered, format="JPEG")
            imagen_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            print(f"Error procesando imagen para SKU {sku}: {e}")
            # Fallback to original if PIL fails
            imagen_b64 = base64.b64encode(fh.getvalue()).decode("utf-8")

        return f"data:image/jpeg;base64,{imagen_b64}"

    return None