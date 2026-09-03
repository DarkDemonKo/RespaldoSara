import os
import subprocess

def lanzar_app_gui(app_command, workspace_num):
    """
    Lanza una ventana GUI (como el navegador) en un workspace específico.
    Aísla estrictamente el entorno clonado sin modificar las variables globales (os.environ).
    """
    user = os.environ.get("USER", "darkdemon")
    try:
        # 1. Buscar el proceso Hyprland del usuario
        pid_output = subprocess.check_output(["pgrep", "-u", user, "-x", "Hyprland"], text=True).strip()
        hyprland_pid = pid_output.split('\n')[0]
    except subprocess.CalledProcessError:
        print(f"No se encontró el proceso Hyprland para {user}.")
        return

    cloned_env = {}
    try:
        # 2. Extraer el entorno de /proc/<PID>/environ
        with open(f"/proc/{hyprland_pid}/environ", "rb") as f:
            for item in f.read().split(b'\0'):
                if b'=' in item:
                    key, value = item.split(b'=', 1)
                    cloned_env[key.decode('utf-8', 'replace')] = value.decode('utf-8', 'replace')
    except Exception as e:
        print(f"Error accediendo al entorno en /proc/{hyprland_pid}/environ: {e}")
        return

    # 3. Aislamiento de Entorno (Sandboxing)
    entorno_modificado = os.environ.copy()
    entorno_modificado.update(cloned_env)

    # 4. Inyectar el entorno modificado EXCLUSIVAMENTE a este proceso gráfico
    comando_lua = f"hl.dsp.exec_cmd('[workspace {workspace_num}] {app_command}')"
    try:
        subprocess.run(
            ["hyprctl", "dispatch", comando_lua],
            env=entorno_modificado,
            check=True
        )
    except Exception as e:
        print(f"Error al lanzar la aplicación gráfica: {e}")


def reproducir_audio(ruta_archivo):
    """
    Restaurar Audio: Llama a paplay/aplay de forma normal.
    Se omite la inyección del entorno gráfico manipulado para evitar romper el subsistema de audio.
    """
    try:
        subprocess.run(["paplay", ruta_archivo], check=True)
    except Exception as e:
        print(f"Error al reproducir audio: {e}")
