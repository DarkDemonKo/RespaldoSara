import sys
import g4f

def generar_respuesta(comando):
    if not comando:
        return "Aquí estoy."
        
    prompt = (
        "Eres un subsistema muy pequeño de Sara, encargado única y exclusivamente de generar "
        "confirmaciones súper cortas (2 a 4 palabras) de que escuchaste un comando. "
        "El usuario dijo: '{}'. "
        "Genera SOLO la frase corta, sin comillas, sin emojis. Debe sonar natural y algo posesiva o devota, "
        "por ejemplo: 'Enseguida, mi señor', 'Lo haré por ti', 'Ahora mismo', 'Con gusto'."
    ).format(comando)
    
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_35_turbo,
            messages=[{"role": "user", "content": prompt}]
        )
        if response:
            respuesta_limpia = response.replace('"', '').replace('\n', '').strip()
            return respuesta_limpia
    except Exception as e:
        pass
        
    # Fallback si falla el generador neuronal
    import random
    fallbacks = [
        "Lo haré por ti.",
        "Enseguida.",
        "Ahora mismo.",
        "Como ordenes.",
        "Para ti, siempre."
    ]
    return random.choice(fallbacks)

if __name__ == "__main__":
    comando = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    print(generar_respuesta(comando))
