import numpy as np
import wave
import os
import time
import subprocess

def play_eponas_song():
    sample_rate = 44100
    volume = 0.5
    
    # Frecuencias de las notas
    D6 = 1174.66
    B5 = 987.77
    A5 = 880.00
    
    # Secuencia de notas (frecuencia, duración, delay posterior)
    melody = [
        (D6, 0.4, 0.05), (B5, 0.4, 0.05), (A5, 1.2, 0.2),
        (D6, 0.4, 0.05), (B5, 0.4, 0.05), (A5, 1.2, 0.2),
        (D6, 0.4, 0.05), (B5, 0.4, 0.05), (A5, 0.8, 0.05), 
        (B5, 0.4, 0.05), (A5, 1.5, 0.0)
    ]
    
    audio_data = []
    
    print("\n===============================================")
    print("🎵 Generando y Reproduciendo: Canción de Epona")
    print("===============================================\n")
    print("⬆️  ⬅️  ➡️    ⬆️  ⬅️  ➡️    ⬆️  ⬅️  ➡️  ⬅️  ➡️\n")

    # Generar la onda completa en un solo arreglo
    for freq, duration, delay in melody:
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        sine = np.sin(freq * t * 2 * np.pi)
        
        # Suavizado de bordes para evitar clicks
        fade = int(sample_rate * 0.05)
        if len(sine) > 2 * fade:
            envelope = np.ones_like(sine)
            envelope[:fade] = np.linspace(0, 1, fade)
            envelope[-fade:] = np.linspace(1, 0, fade)
            sine *= envelope
            
        audio_data.append(sine)
        
        # Agregar silencio
        if delay > 0:
            audio_data.append(np.zeros(int(sample_rate * delay)))
            
    # Concatenar y convert a 16 bits
    full_audio = np.concatenate(audio_data)
    full_audio = (full_audio * volume * 32767).astype(np.int16)
    
    # Guardar a archivo temporal WAV
    wav_path = "/tmp/epona_melody.wav"
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(1)      # Mono
        wav_file.setsampwidth(2)      # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(full_audio.tobytes())
        
    # Reproducir con el sistema nativo de audio (PulseAudio/PipeWire)
    subprocess.run(["paplay", wav_path])
    
    print("¡Un caballo se acerca a lo lejos! 🐎\n")

if __name__ == "__main__":
    play_eponas_song()
