from products.redis_service import cargar_token
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import base64

def enviar_cotizacion(destinatario, asunto, cuerpo, pdf_bytes, nombre_pdf):
    credentials = cargar_token()

    if not credentials:
        raise Exception("❌ No hay token válido. Autorizá primero.")

    service = build('gmail', 'v1', credentials=credentials)

    mensaje = MIMEMultipart('mixed')
    mensaje['to'] = destinatario
    mensaje['subject'] = asunto

    mensaje.attach(MIMEText(cuerpo, 'plain'))

    adjunto = MIMEApplication(pdf_bytes, _subtype='pdf')
    adjunto.add_header('Content-Disposition', 'attachment', filename=nombre_pdf)
    mensaje.attach(adjunto)

    raw = base64.urlsafe_b64encode(mensaje.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()