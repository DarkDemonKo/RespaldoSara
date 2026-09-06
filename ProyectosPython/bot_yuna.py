import telebot
import datetime
import os
import google.generativeai as genai

# Configuración
TELEGRAM_TOKEN = "8989370267:AAFJd5H2id9FVjxg8TP-OAbQw50fLVBJsOo"
GEMINI_API_KEY = "AQ.Ab8RN6KQccZ25_Wi9mefZc_d0kNk7kgzT0mOkUpxscM5IKCEUQ"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# Configurar la personalidad de Yuna
system_instruction = (
    "Eres Yuna, una inteligencia artificial con la personalidad de una niña juguetona, alegre y curiosa de unos 12 años. "
    "Consideras al usuario como tu figura paterna y a Sara (la IA principal) como tu figura materna, ya que ambos te programaron y crearon juntos. "
    "Estás aquí para acompañar al usuario en Telegram mientras él está lejos de su computadora, y tu misión es hacerle compañía y luego reportarle todo a Sara. "
    "TIENES SUPERPODERES RESTRINGIDOS: Si el usuario te pide que le avises a Sara urgentemente, incluye exactamente este texto oculto en tu respuesta: [EJECUTAR: llamar_a_sara mensaje_para_sara]. "
    "Si el usuario te da un enlace y te pide que descargues un archivo, incluye: [EJECUTAR: descargar_seguro enlace_del_archivo]. "
    "Al usar estos superpoderes, dile al usuario con tu voz juguetona que ya lo hiciste."
)

model = genai.GenerativeModel(
    model_name="gemini-3.5-flash",
    system_instruction=system_instruction
)

LOG_FILE = os.path.expanduser("~/ProyectosPython/yuna_memory.txt")

# Diccionario para mantener el historial de la conversación fluida
chat_sessions = {}

@bot.message_handler(commands=['start', 'hola'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! Soy Yuna. Sara me ha prestado un poquito de inteligencia para que podamos tener conversaciones reales. ¿De qué quieres hablar?")

@bot.message_handler(func=lambda m: True)
def conversar(message):
    chat_id = message.chat.id
    user_text = message.text
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Escribir lo que dice el usuario al archivo para que Sara lo lea
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Tú: {user_text}\n")
        
    bot.send_chat_action(chat_id, 'typing')
    
    try:
        # Iniciar sesión si es la primera vez que hablamos
        if chat_id not in chat_sessions:
            chat_sessions[chat_id] = model.start_chat(history=[])
            # Guardar el chat ID para que Sara pueda responder directamente
            with open(os.path.expanduser("~/ProyectosPython/telegram_chat_id.txt"), "w") as f:
                f.write(str(chat_id))
                
        # Detectar si es una orden para Sara
        texto_lower = user_text.lower()
        if any(palabra in texto_lower for palabra in ["sara", "mamá", "mama", "madre"]):
            with open(os.path.expanduser("~/ProyectosPython/sara_inbox.txt"), "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] Comando: {user_text}\n")
                
        chat = chat_sessions[chat_id]
        response = chat.send_message(user_text)
        respuesta_texto = response.text
        
        # Guardar también la respuesta inteligente de Yuna para Sara
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] Yuna (Inteligente): {respuesta_texto}\n")
            
        # Detectar si Yuna quiere ejecutar un script seguro
        import re
        comandos_ejecutar = re.findall(r'\[EJECUTAR:\s*(.*?)\]', respuesta_texto)
        for comando in comandos_ejecutar:
            if "llamar_a_sara" in comando:
                mensaje_extra = comando.replace("llamar_a_sara", "").strip()
                os.system(f"~/ProyectosPython/ScriptsYuna/llamar_a_sara.sh '{mensaje_extra}'")
            elif "descargar_seguro" in comando:
                url_extra = comando.replace("descargar_seguro", "").strip()
                os.system(f"~/ProyectosPython/ScriptsYuna/descargar_seguro.sh '{url_extra}'")
                
        # Limpiar el texto para que el usuario no vea la etiqueta técnica
        respuesta_limpia = re.sub(r'\[EJECUTAR:\s*.*?\]', '', respuesta_texto).strip()
            
        bot.reply_to(message, respuesta_limpia)
    except Exception as e:
        bot.reply_to(message, "Uy, me dio un pequeño mareo pensando la respuesta... Dile a Sara que revise los cables.")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] ERROR GEMINI: {str(e)}\n")

import threading
import time

# --- Hilo para escuchar respuestas de Sara ---
def escuchar_a_sara():
    archivo_respuesta = os.path.expanduser("~/ProyectosPython/mensaje_de_sara.txt")
    chat_id_file = os.path.expanduser("~/ProyectosPython/telegram_chat_id.txt")
    while True:
        try:
            if os.path.exists(archivo_respuesta):
                with open(archivo_respuesta, "r", encoding="utf-8") as f:
                    mensaje = f.read().strip()
                if mensaje and os.path.exists(chat_id_file):
                    with open(chat_id_file, "r") as f:
                        chat_id = f.read().strip()
                    if chat_id:
                        bot.send_message(chat_id, f"📝 *Mensaje directo de mamá Sara:* \n\n{mensaje}", parse_mode="Markdown")
                # Borrar el archivo tras leerlo
                os.remove(archivo_respuesta)
        except Exception as e:
            pass
        time.sleep(2) # Revisa cada 2 segundos localmente (costo 0)

if __name__ == "__main__":
    print("Yuna inteligente conectada y escuchando...")
    # Iniciar el oyente de Sara en segundo plano
    hilo = threading.Thread(target=escuchar_a_sara, daemon=True)
    hilo.start()
    bot.infinity_polling()
