def type_text(text):
    if not text.strip(): return
    import subprocess
    import os
    import time

    TMUX_SESSION = "sara_agent"

    # Verificar si la sesión de tmux ya existe (socket UNIX local activo)
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

        # Invocamos la ventana foot, pero envolviendo agy en un servidor tmux
        tmux_cmd = f"tmux new-session -s {TMUX_SESSION} 'agy --dangerously-skip-permissions'"
        subprocess.Popen(['foot', '-a', 'org.omarchy.agent', 'sh', '-c', tmux_cmd], env=env)
        
        # Esperar a que el servidor de tmux inicialice el PTY y cargue agy
        time.sleep(1.5)

    # Inyección Headless real a través de Socket UNIX:
    # Envía el texto escrito directamente al PTY de agy, y presiona Enter ('C-m' o 'Enter')
    # Todo esto ocurre sin robar el foco de Wayland/Hyprland ni usar wtype.
    subprocess.run(['tmux', 'send-keys', '-t', TMUX_SESSION, text, 'Enter'])
