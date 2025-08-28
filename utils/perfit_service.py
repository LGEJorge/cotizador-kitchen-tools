import requests
import os

list_id = 3
account = "kitchentoolsv"
api_key = os.environ.get("PERFIT_API_KEY")

url = f"https://api.myperfit.com/v2/{account}/lists/{list_id}/contacts"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def cargar_contacto_prefit(mail, cliente, telefono, rubro):
    contact_data = {
        "email": mail,
        "firstName": cliente,
        "lastName": "",
        "customFields": [
            {"id": 11, "value": telefono}, #Telefono
            {"id": 12, "value": rubro} #Rubro
        ],
        "interests": []
    }
    
    response = requests.post(url, json=contact_data, headers=headers)

    if response.status_code == 201 :
        contact = response.json().get("data")
        print("✅ Contacto creado/actualizado:", contact)
    else:
        print("❌ Error al crear el contacto:", response.status_code, response.text)