import numpy as np
import wave
import os
import subprocess

def create_square_wave(freq, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # Generar onda senoidal y convertirla a onda cuadrada (1 o -1)
    sine = np.sin(freq * t * 2 * np.pi)
    square = np.sign(sine)
    
    # Suavizado súper corto para mantener el estilo 8-bits brusco sin que truene la bocina
    fade = int(sample_rate * 0.005)
    if len(square) > 2 * fade:
        envelope = np.ones_like(square)
        envelope[:fade] = np.linspace(0, 1, fade)
        envelope[-fade:] = np.linspace(1, 0, fade)
        square *= envelope
        
    return square

def play_eponas_song_8bit():
    sample_rate = 44100
    # Las ondas cuadradas suenan MUCHO más fuerte que las senoidales, bajamos el volumen
    volume = 0.15 
    
    D6, B5, A5 = 1174.66, 987.77, 880.00
    
    melody = [
        # Parte 1
        (D6, 0.4, 0.05), (B5, 0.4, 0.05), (A5, 1.2, 0.2),
        # Parte 2
        (D6, 0.4, 0.05), (B5, 0.4, 0.05), (A5, 1.2, 0.2),
        # Parte 3
        (D6, 0.4, 0.05), (B5, 0.4, 0.05), (A5, 0.8, 0.05), (B5, 0.4, 0.05), (A5, 1.5, 0.0)
    ]
    
    melody = melody * 3
    audio_data = []
    print("\n===============================================")
    print("🕹️ Generando versión 8-BITS (Retro) de Epona...")
    print("===============================================\n")
    
    for freq, duration, delay in melody:
        square = create_square_wave(freq, duration, sample_rate)
        audio_data.append(square)
        if delay > 0:
            audio_data.append(np.zeros(int(sample_rate * delay)))
            
    full_audio = np.concatenate(audio_data)
    full_audio = (full_audio * volume * 32767).astype(np.int16)
    
    wav_path = "/tmp/epona_8bit.wav"
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(full_audio.tobytes())
        
    subprocess.run(["paplay", wav_path])

if __name__ == "__main__":
    play_eponas_song_8bit()
