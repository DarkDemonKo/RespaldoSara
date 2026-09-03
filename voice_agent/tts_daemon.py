import os
import json
import time
import glob
import subprocess
import re

def get_latest_transcripts():
    paths = [
        os.path.expanduser("~/.gemini/antigravity-cli/brain/*/.system_generated/logs/transcript_full.jsonl"),
        os.path.expanduser("~/.gemini/antigravity/brain/*/.system_generated/logs/transcript_full.jsonl"),
        os.path.expanduser("~/.gemini/antigravity-ide/brain/*/.system_generated/logs/transcript_full.jsonl"),
    ]
    files = []
    for p in paths:
        files.extend(glob.glob(p))
    return files

def tail_files():
    file_sizes = {}
    for f in get_latest_transcripts():
        try:
            file_sizes[f] = os.path.getsize(f)
        except OSError:
            pass

    conversation_voice_mode = {}

    print("Listening for AI responses...")
    while True:
        current_files = get_latest_transcripts()
        for f in current_files:
            try:
                size = os.path.getsize(f)
                if f not in file_sizes:
                    # New conversation started, read from start
                    file_sizes[f] = 0
                
                if size > file_sizes[f]:
                    with open(f, 'r', encoding='utf-8') as fp:
                        fp.seek(file_sizes[f])
                        new_data = fp.read()
                        file_sizes[f] = size
                        
                        for line in new_data.strip().split('\n'):
                            if not line: continue
                            try:
                                data = json.loads(line)
                                
                                # 1. Detectar el origen del prompt
                                if data.get('type') == 'USER_INPUT':
                                    input_content = data.get('content', '')
                                    if '[VOICE_INPUT]' in input_content:
                                        conversation_voice_mode[f] = True
                                    else:
                                        conversation_voice_mode[f] = False

                                # 2. Condicional TTS: Solo hablar si la conversación activa proviene de voz
                                if data.get('type') == 'PLANNER_RESPONSE':
                                    if conversation_voice_mode.get(f, False):
                                        content = data.get('content', '')
                                        if content:
                                            # Clean up markdown for TTS
                                            clean_content = re.sub(r'[*`#_-]', '', content)
                                            clean_content = re.sub(r'http\S+', '', clean_content)
                                            # Use Piper TTS for a natural neural voice
                                            with open('/tmp/sara_speaking.lock', 'w') as f_lock:
                                                f_lock.write('1')
                                                
                                            piper_cmd = [
                                                os.path.expanduser('~/.config/omarchy/voice_agent/piper/piper/piper'),
                                                '-m',
                                                os.path.expanduser('~/.config/omarchy/voice_agent/piper/daniela/model.onnx'),
                                                '--output_raw'
                                            ]
                                            aplay_cmd = ['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-']
                                            
                                            p_piper = subprocess.Popen(piper_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                                            p_aplay = subprocess.Popen(aplay_cmd, stdin=p_piper.stdout)
                                            p_piper.stdin.write(clean_content.encode('utf-8'))
                                            p_piper.stdin.close()
                                            
                                            p_aplay.wait()
                                            p_piper.wait()
                                            if os.path.exists('/tmp/sara_speaking.lock'):
                                                os.remove('/tmp/sara_speaking.lock')
                            except Exception as e:
                                pass
            except OSError:
                pass
        time.sleep(1)

if __name__ == "__main__":
    tail_files()
