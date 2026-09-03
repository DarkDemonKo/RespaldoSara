import sys
import os
import queue
import json
import subprocess
import time

os.environ["VOSK_LOG_LEVEL"] = "-1"
import vosk
import sounddevice as sd

MODEL_PATH = os.path.expanduser("~/.config/omarchy/voice_agent/model")


def say_esta_bien(comando=""):
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
            
        # Llamar al subsistema neuronal independiente
        gen_script = os.path.expanduser('~/ProyectosPython/generador_respuestas_sara.py')
        python_exe = os.path.expanduser('~/ProyectosPython/entorno_voz/bin/python')
        result = subprocess.run([python_exe, gen_script, comando], capture_output=True, text=True)
        frase = result.stdout.strip() if result.stdout.strip() else "Aquí estoy."
        
        p_piper = subprocess.Popen(piper_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        p_aplay = subprocess.Popen(aplay_cmd, stdin=p_piper.stdout)
        
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

        # Invocamos la ventana con tmux instanciando Antigravity
        tmux_cmd = f"tmux new-session -s {TMUX_SESSION} 'agy --dangerously-skip-permissions'"
        subprocess.Popen(['foot', '-a', 'org.omarchy.agent', 'sh', '-c', tmux_cmd], env=env)
        
        # FIX BUG 1: Polling activo para evitar la condición de carrera por "Cold Start"
        ready = False
        start_time = time.time()
        while time.time() - start_time < 5.0:  # Hasta 5 segundos de espera máxima
            # 1. Comprobar que tmux ya registró la sesión (proceso e IPC listos)
            tmux_ready = subprocess.run(
                ['tmux', 'has-session', '-t', TMUX_SESSION], 
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ).returncode == 0
            
            if tmux_ready:
                # 2. Comprobar que hyprland mapeó la ventana de la terminal (foot)
                try:
                    clients_out = subprocess.check_output(['hyprctl', 'clients', '-j'])
                    clients = json.loads(clients_out)
                    if any(c.get('class') == 'org.omarchy.agent' for c in clients):
                        # 3. Comprobar que agy está completamente inicializado leyendo el TTY
                        capture = subprocess.check_output(['tmux', 'capture-pane', '-p', '-t', TMUX_SESSION], stderr=subprocess.DEVNULL).decode()
                        if 'for shortcuts' in capture or '>' in capture:
                            ready = True
                            break
                except Exception:
                    pass
            time.sleep(0.1)
        
        if not ready:
            # Fallback en caso de que el gestor tarde más o haya fallado el polling
            time.sleep(1.0)

    # Inyección headless: Enviamos el texto etiquetado directamente al pseudo-terminal (PTY)
    tagged_text = f"[VOICE_INPUT] {text}"
    subprocess.run(['tmux', 'send-keys', '-t', TMUX_SESSION, tagged_text, 'Enter'])



def play_beep():
    subprocess.Popen(['paplay', '/usr/share/sounds/freedesktop/stereo/message.oga'])

def start_listening():
    q = queue.Queue()
    def callback(indata, frames, time, status):
        q.put(bytes(indata))

    while True:
        try:
            model = vosk.Model(MODEL_PATH)
            samplerate = int(sd.query_devices(None, 'input')['default_samplerate'])
            rec = vosk.KaldiRecognizer(model, samplerate)
            
            subprocess.run(['notify-send', 'Sara (Voz)', '👂 Lista. Di "Sara" para activarme.'])

            state = "WAITING_FOR_WAKEWORD"
            command_chunks = []
            silence_timer = time.time()

            with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16', channels=1, callback=callback):
                while True:
                    data = q.get()
                    if os.path.exists('/tmp/sara_speaking.lock'):
                        rec.Reset()
                        continue
                        
                    if rec.AcceptWaveform(data):
                        res = json.loads(rec.Result())
                        text = res.get('text', '')
                        
                        if state == "WAITING_FOR_WAKEWORD":
                            if not text: continue
                            words = text.lower().split()
                            wake_words = ["sara", "sarah", "zara", "sahra"]
                            if any(w in words for w in wake_words):
                                play_beep()
                                state = "LISTENING_COMMAND"
                                
                                idx = -1
                                for w in wake_words:
                                    if w in words:
                                        idx = words.index(w)
                                        break
                                first_part = " ".join(words[idx+1:]).strip()
                                if first_part:
                                    command_chunks.append(first_part)
                                
                                silence_timer = time.time()
                        
                        elif state == "LISTENING_COMMAND":
                            if text:
                                command_chunks.append(text)
                                silence_timer = time.time()
                            
                            if time.time() - silence_timer > 2.5:
                                final_command = " ".join(command_chunks).strip()
                                if final_command:
                                    subprocess.run(['notify-send', 'Sara', 'Procesando tu solicitud...'])
                                    say_esta_bien(final_command)
                                    type_text(final_command)
                                
                                state = "WAITING_FOR_WAKEWORD"
                                command_chunks = []
                                rec.Reset()
                    else:
                        if state == "LISTENING_COMMAND":
                            partial = json.loads(rec.PartialResult()).get('partial', '')
                            if partial:
                                silence_timer = time.time()
                            elif time.time() - silence_timer > 3.0:
                                final_command = " ".join(command_chunks).strip()
                                if final_command:
                                    subprocess.run(['notify-send', 'Sara', 'Procesando tu solicitud...'])
                                    say_esta_bien(final_command)
                                    type_text(final_command)
                                state = "WAITING_FOR_WAKEWORD"
                                command_chunks = []
                                rec.Reset()

        except Exception as e:
            time.sleep(2)

if __name__ == '__main__':
    start_listening()
