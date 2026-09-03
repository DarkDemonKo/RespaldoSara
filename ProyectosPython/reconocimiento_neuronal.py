import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import numpy as np
import tempfile
import os
import queue
import sys

print("Cargando el modelo neuronal (Whisper base)... esto tomará unos segundos la primera vez.")
# "base" es rápido y ligero. Si quieres más precisión después, puedes cambiarlo a "small" o "medium".
model_size = "base"
model = WhisperModel(model_size, device="cpu", compute_type="int8")
print("🧠 ¡Red neuronal cargada y lista!")

q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())

def grabar_hasta_interrupcion(samplerate=16000, channels=1):
    print("\n🎤 Grabando... (Presiona Ctrl+C para detener la grabación y transcribir lo que dijiste)")
    try:
        with sd.InputStream(samplerate=samplerate, channels=channels, dtype='int16', callback=callback):
            while True:
                pass
    except KeyboardInterrupt:
        print("\nProcesando el audio con neuronas artificiales...")
        
    # Recopilar datos de la cola
    data = []
    while not q.empty():
        data.append(q.get())
    
    if len(data) == 0:
        return None
        
    audio_data = np.concatenate(data, axis=0)
    
    # Guardar en archivo temporal para que Whisper lo lea
    _, temp_path = tempfile.mkstemp(suffix=".wav")
    write(temp_path, samplerate, audio_data)
    return temp_path

if __name__ == "__main__":
    try:
        while True:
            # Limpiar la cola por si quedó algo de antes
            with q.mutex:
                q.queue.clear()
                
            ruta = grabar_hasta_interrupcion()
            if not ruta:
                continue
                
            # Transcribir usando Whisper (indicamos que el idioma es español)
            segments, info = model.transcribe(ruta, beam_size=5, language="es")
            
            print("\n" + "="*50)
            print("🤖 Lo que escuchó la red neuronal (Whisper):")
            texto = ""
            for segment in segments:
                texto += segment.text + " "
            print(f"'{texto.strip()}'")
            print("="*50 + "\n")
            
            # Limpiar archivo temporal
            os.remove(ruta)
            
            respuesta = input("¿Quieres hacer otra prueba de voz? (s/n): ")
            if respuesta.lower() != 's':
                break
    except KeyboardInterrupt:
        print("\nSaliendo del programa... ¡Hasta luego!")
