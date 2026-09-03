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
        print(f"Error: La sesión de tmux '{TMUX_SESSION}' no existe. No se puede inyectar texto.")
        return

    # Inyección headless: Enviamos el texto directamente al pseudo-terminal (PTY)
    subprocess.run(['tmux', 'send-keys', '-t', TMUX_SESSION, text, 'Enter'])


def launch_gui_app(command_args):
    """
    FIX BUG 2: Ejecuta una aplicación gráfica asegurando que se abra en el workspace activo de Hyprland.
    :param command_args: Lista con el comando y sus argumentos o string, ej: ['firefox', '--private-window']
    """
    import json
    import subprocess
    import shlex
    
    # Convertir a string escapado de manera segura si es una lista
    if isinstance(command_args, list):
        cmd_str = ' '.join(shlex.quote(arg) for arg in command_args)
    else:
        cmd_str = command_args

    try:
        # 1. Obtener el workspace activo directamente de Hyprland
        ws_out = subprocess.check_output(['hyprctl', 'activeworkspace', '-j'])
        ws_data = json.loads(ws_out)
        active_workspace_id = ws_data.get('id')
        
        if active_workspace_id is not None:
            # 2. Construir la regla de ejecución de Hyprland (hyprctl dispatch exec "[workspace ID] comando")
            hyprctl_cmd = f"[workspace {active_workspace_id}] {cmd_str}"
            subprocess.Popen(['hyprctl', 'dispatch', 'exec', hyprctl_cmd])
            return
    except Exception as e:
        # Silenciar error y pasar al fallback
        pass
        
    # Fallback: Ejecución directa usando Popen normal en caso de fallo (ej. entorno sin Hyprland)
    if isinstance(command_args, list):
        subprocess.Popen(command_args)
    else:
        subprocess.Popen(command_args, shell=True)
