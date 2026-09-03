import subprocess
import os

def get_wayland_env():
    env_vars = ['WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR', 'HYPRLAND_INSTANCE_SIGNATURE']
    extracted_env = {}
    try:
        # Find foot PID
        pids = subprocess.check_output(['pgrep', 'foot']).decode().strip().split('\n')
        for pid in pids:
            with open(f'/proc/{pid}/environ', 'rb') as f:
                environ_data = f.read().split(b'\0')
                for item in environ_data:
                    if b'=' in item:
                        key, val = item.split(b'=', 1)
                        key = key.decode('utf-8', errors='ignore')
                        val = val.decode('utf-8', errors='ignore')
                        if key in env_vars:
                            extracted_env[key] = val
            if len(extracted_env) == 3:
                break
    except Exception as e:
        print(f"Error fetching child env: {e}")
    
    return extracted_env

print(get_wayland_env())
