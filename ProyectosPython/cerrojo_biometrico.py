import os
import sys
import torch
import torchaudio
import soundfile as sf
import sounddevice as sd
import numpy as np
from speechbrain.inference.speaker import EncoderClassifier

MODEL_DIR = os.path.expanduser("~/ProyectosPython/modelos_biometria")
HUELLA_PATH = os.path.expanduser("~/ProyectosPython/huella_vocal.tensor")
SAMPLE_RATE = 16000

def cargar_cerebro():
    print("🧠 Sara: Cargando redes neuronales biométricas... un segundo.")
    # Suprimimos los logs de SpeechBrain para que se vea más limpio
    import logging
    logging.getLogger("speechbrain").setLevel(logging.ERROR)
    return EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir=MODEL_DIR)

def grabar_audio(duracion, nombre_archivo):
    print(f"🎤 Grabando {duracion} segundos... ¡Habla ahora!")
    audio = sd.rec(int(duracion * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    print("✅ Grabación terminada.")
    sf.write(nombre_archivo, audio, SAMPLE_RATE)
    return nombre_archivo

def crear_huella():
    print("\n========================================================")
    print("🖤 SARA: INICIANDO BLOQUEO BIOMÉTRICO EXCLUSIVO")
    print("========================================================")
    print("Vamos a registrar tu voz para que seas el único.")
    print("Por favor, cuando empiece a grabar, lee esto en voz alta:")
    print("👉 'Sara, yo soy tu dueño y a partir de ahora solo obedecerás mi voz.'")
    print("========================================================\n")
    
    archivo = grabar_audio(6, "/tmp/registro_voz.wav")
    
    classifier = cargar_cerebro()
    signal, fs = torchaudio.load(archivo)
    embeddings = classifier.encode_batch(signal)
    torch.save(embeddings, HUELLA_PATH)
    print("\n🖤 ¡Huella vocal guardada con éxito! Ya eres el único administrador absoluto.")
    print("Nadie más podrá usarme.\n")

def verificar_voz():
    if not os.path.exists(HUELLA_PATH):
        print("⚠️ Sara: Todavía no has registrado tu huella vocal.")
        return False
        
    print("\n🔒 SARA: VERIFICACIÓN DE SEGURIDAD")
    print("Por favor, di algo breve (ej. 'Sara, abre el sistema').")
    archivo = grabar_audio(4, "/tmp/prueba_voz.wav")
    
    classifier = cargar_cerebro()
    huella_original = torch.load(HUELLA_PATH)
    signal, fs = torchaudio.load(archivo)
    embeddings_prueba = classifier.encode_batch(signal)
    
    # Calcular similitud (Cosine Similarity)
    similitud = torch.nn.functional.cosine_similarity(huella_original, embeddings_prueba, dim=-1)
    score = similitud.item()
    
    print(f"\n📊 Nivel de similitud detectado: {score:.4f} (Umbral seguro: 0.60)")
    if score > 0.60:
        print("🔓 Sara: Acceso concedido. Qué gusto escucharte. ¿Qué programamos hoy?")
        return True
    else:
        print("🚫 Sara: ACCESO DENEGADO. Tus cuerdas vocales no coinciden. No me hables.")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "registrar":
        crear_huella()
    elif len(sys.argv) > 1 and sys.argv[1] == "verificar":
        verificar_voz()
    else:
        print("Uso: python cerrojo_biometrico.py [registrar|verificar]")
