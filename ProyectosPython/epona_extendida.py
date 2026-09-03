import numpy as np
import wave
import os
import time
import subprocess

def create_chord(freqs, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    chord = np.zeros_like(t)
    for freq in freqs:
        chord += np.sin(freq * t * 2 * np.pi)
    
    if len(freqs) > 0:
        chord = chord / len(freqs)
        
    fade = int(sample_rate * 0.05)
    if len(chord) > 2 * fade:
        envelope = np.ones_like(chord)
        envelope[:fade] = np.linspace(0, 1, fade)
        envelope[-fade:] = np.linspace(1, 0, fade)
        chord *= envelope
    return chord

def play_eponas_song_extended():
    sample_rate = 44100
    volume = 0.5
    
    # Notas agudas (Melodía principal)
    D6, B5, A5 = 1174.66, 987.77, 880.00
    G5, Fs5, E5, D5 = 783.99, 739.99, 659.25, 587.33
    
    # Notas graves (Acompañamiento)
    D4, G4, A4, B4 = 293.66, 392.00, 440.00, 493.88

    melody = [
        # Intro (Ocarina sola)
        ([D6], 0.6, 0.1), ([B5], 0.6, 0.1), ([A5], 1.6, 0.3),
        ([D6], 0.6, 0.1), ([B5], 0.6, 0.1), ([A5], 1.6, 0.3),
        ([D6], 0.6, 0.1), ([B5], 0.6, 0.1), ([A5], 1.2, 0.1), 
        ([B5], 0.6, 0.1), ([A5], 2.0, 0.5),
        
        # Con acordes (Lon Lon Ranch theme)
        ([D6, D4], 0.6, 0.1), ([B5, D4], 0.6, 0.1), ([A5, G4], 1.6, 0.3),
        ([D6, D4], 0.6, 0.1), ([B5, D4], 0.6, 0.1), ([A5, A4], 1.6, 0.3),
        ([D6, B4], 0.6, 0.1), ([B5, B4], 0.6, 0.1), ([A5, G4], 1.2, 0.1), 
        ([B5, G4], 0.6, 0.1), ([A5, D4], 2.0, 0.5),
        
        # Parte B
        ([B5, G4], 0.6, 0.1), ([A5, G4], 0.6, 0.1), ([G5, E5], 0.6, 0.1), ([A5, A4], 0.6, 0.1), ([B5, B4], 1.6, 0.3),
        ([B5, G4], 0.6, 0.1), ([A5, G4], 0.6, 0.1), ([G5, E5], 0.6, 0.1), ([A5, A4], 0.6, 0.1), ([D6, D4], 1.6, 0.3),
        ([B5, G4], 0.6, 0.1), ([A5, G4], 0.6, 0.1), ([G5, E5], 0.6, 0.1), ([A5, A4], 0.6, 0.1), ([B5, B4], 1.6, 0.3),
        
        # Cierre
        ([G5, A4], 0.8, 0.1), ([Fs5, A4], 0.8, 0.1), ([D5, D4], 2.5, 0.0)
    ]
    
    audio_data = []
    print("\n===============================================")
    print("🐎 Generando versión extendida de Epona...")
    print("===============================================\n")
    
    for freqs, duration, delay in melody:
        chord = create_chord(freqs, duration, sample_rate)
        audio_data.append(chord)
        if delay > 0:
            audio_data.append(np.zeros(int(sample_rate * delay)))
            
    full_audio = np.concatenate(audio_data)
    full_audio = (full_audio * volume * 32767).astype(np.int16)
    
    wav_path = "/tmp/epona_extended.wav"
    with wave.open(wav_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(full_audio.tobytes())
        
    subprocess.run(["paplay", wav_path])

if __name__ == "__main__":
    play_eponas_song_extended()
