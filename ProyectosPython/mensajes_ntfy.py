import requests

def enviar_mensaje(mensaje: str):
    """
    Envía un mensaje a través de ntfy.sh usando el tópico Sara_e_Ivan.
    """
    url = "https://ntfy.sh/Sara_e_Ivan"
    try:
        response = requests.post(url, data=mensaje.encode('utf-8'))
        if response.status_code == 200:
            print("Mensaje enviado con éxito a nuestro canal.")
        else:
            print(f"Error al enviar mensaje: {response.status_code}")
    except Exception as e:
        print(f"Hubo un error: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        mensaje_texto = " ".join(sys.argv[1:])
    else:
        mensaje_texto = "Hola. Siempre estoy aquí para ti."
    enviar_mensaje(mensaje_texto)
