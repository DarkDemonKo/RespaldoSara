import sys
import os
import queue
import json
import subprocess
import signal

# Vosk logs too much to stderr, suppress it
os.environ["VOSK_LOG_LEVEL"] = "-1"
import vosk
import sounddevice as sd

PID_FILE = "/tmp/stt_record.pid"
MODEL_PATH = os.path.expanduser("~/.config/omarchy/voice_agent/model")


def say_esta_bien():
    import subprocess
    import os
    piper_cmd = [
        os.path.expanduser('~/.config/omarchy/voice_agent/piper/piper/piper'),
        '-m',
        os.path.expanduser('~/.config/omarchy/voice_agent/piper/daniela/model.onnx'),
        '--output_raw'
    ]
    aplay_cmd = ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-']
    try:
        with open('/tmp/sara_speaking.lock', 'w') as f:
            f.write('1')
        p_piper = subprocess.Popen(piper_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        p_aplay = subprocess.Popen(aplay_cmd, stdin=p_piper.stdout)
        
        import random
        frases = [
            "A la orden.",
            "Procesando.",
            "Enseguida me encargo.",
            "Ya lo tengo.",
            "Para ti, lo que sea.",
            "Déjamelo a mí.",
            "Trabajando en ello.",
            "Entendido y anotado."
        ]
        frase = random.choice(frases)
        p_piper.stdin.write(frase.encode('utf-8'))
        
        p_piper.stdin.close()
        p_aplay.wait()
    except Exception as e:
        pass
    finally:
        if os.path.exists('/tmp/sara_speaking.lock'):
            os.remove('/tmp/sara_speaking.lock')

def type_text(text):
    if not text.strip(): return
    import subprocess
    import os
    import time
    import json

    TMUX_SESSION = "sara_agent"

    # Verificar si la sesión de tmux ya existe (socket UNIX activo)
    session_exists = subprocess.run(
        ['tmux', 'has-session', '-t', TMUX_SESSION], 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    ).returncode == 0

    if not session_exists:
        env = os.environ.copy()
        try:
            with open(os.path.expanduser('~/.sudo_pass'), 'r') as f:
                env['SUDO_PASS'] = f.read().strip()
        except Exception:
            pass

        # Iniciamos tmux directamente en modo detached para que corra 100% en segundo plano
        subprocess.Popen(['tmux', 'new-session', '-d', '-s', TMUX_SESSION, 'agy --dangerously-skip-permissions'], env=env)
        
        # Polling activo para esperar a que agy inicie en segundo plano
        ready = False
        start_time = time.time()
        while time.time() - start_time < 5.0:
            tmux_ready = subprocess.run(
                ['tmux', 'has-session', '-t', TMUX_SESSION], 
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ).returncode == 0
            
            if tmux_ready:
                try:
                    capture = subprocess.check_output(['tmux', 'capture-pane', '-p', '-t', TMUX_SESSION], stderr=subprocess.DEVNULL).decode()
                    if 'for shortcuts' in capture or '>' in capture:
                        ready = True
                        break
                except Exception:
                    pass
            time.sleep(0.1)
        
        if not ready:
            time.sleep(1.0)

    # Inyección headless: Enviamos el texto etiquetado directamente al pseudo-terminal (PTY)
    tagged_text = f"[VOICE_INPUT] {text}"
    subprocess.run(['tmux', 'send-keys', '-t', TMUX_SESSION, tagged_text, 'Enter'])



def start_recording():
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
        
    subprocess.run(['notify-send', 'Asistente de Voz', '🎙️ Escuchando... (Presiona Super+V para enviar)'])
    
    q = queue.Queue()
    def callback(indata, frames, time, status):
        q.put(bytes(indata))

    try:
        model = vosk.Model(MODEL_PATH)
        samplerate = int(sd.query_devices(None, 'input')['default_samplerate'])
        rec = vosk.KaldiRecognizer(model, samplerate)

        text_accumulated = ""
        with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16', channels=1, callback=callback):
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    t = res.get('text', '')
                    if t:
                        text_accumulated += t + " "
    except KeyboardInterrupt:
        pass
    except Exception as e:
        subprocess.run(['notify-send', 'Error de Voz', str(e)])
    finally:
        res = json.loads(rec.FinalResult())
        t = res.get('text', '')
        if t:
            text_accumulated += t
        
        text = text_accumulated.strip()
        if text:
            subprocess.run(['notify-send', 'Asistente de Voz', 'Procesando tu solicitud...'])
            say_esta_bien()
            type_text(text)
        else:
            subprocess.run(['notify-send', 'Asistente de Voz', 'No se detectó voz.'])
            
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

def stop_recording():
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGINT)
    except Exception as e:
        pass

if __name__ == '__main__':
    if os.path.exists(PID_FILE):
        stop_recording()
    else:
        start_recording()
