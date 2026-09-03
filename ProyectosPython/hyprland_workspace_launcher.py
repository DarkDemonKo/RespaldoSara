import subprocess
import os

def ejecutar_app_en_workspace(app: str, workspace: str) -> None:
    """
    Clona el entorno exacto del proceso padre de Hyprland para garantizar
    que las variables clave (WAYLAND_DISPLAY, HYPRLAND_INSTANCE_SIGNATURE, DBUS_SESSION_BUS_ADDRESS)
    estén presentes, y ejecuta una aplicación en un workspace específico utilizando
    reglas inline.
    """
    # 1. Encontrar el PID maestro de Hyprland
    user = os.environ.get("USER", "darkdemon")
    try:
        # Usamos pgrep para encontrar el proceso Hyprland del usuario
        pid_output = subprocess.check_output(["pgrep", "-u", user, "-x", "Hyprland"], text=True).strip()
        hyprland_pid = pid_output.split('\n')[0]
    except subprocess.CalledProcessError:
        raise RuntimeError(f"No se encontró el proceso Hyprland en ejecución para el usuario '{user}'.")

    # 2. Extraer y clonar el entorno absoluto desde /proc/<PID>/environ
    try:
        with open(f"/proc/{hyprland_pid}/environ", "rb") as f:
            env_bytes = f.read()
    except Exception as e:
        raise RuntimeError(f"No se pudo acceder al entorno en /proc/{hyprland_pid}/environ: {e}")

    cloned_env = {}
    # Los items en environ están separados por un byte nulo (\0)
    for item in env_bytes.split(b'\0'):
        if b'=' in item:
            key, value = item.split(b'=', 1)
            cloned_env[key.decode('utf-8', 'replace')] = value.decode('utf-8', 'replace')

    # Partimos del entorno base y lo sobreescribimos completamente con el entorno clonado
    # Esto garantiza que cualquier daemon o proceso hijo adquiera DBUS, WAYLAND y HYPRLAND vars correctas.
    final_env = os.environ.copy()
    final_env.update(cloned_env)

    # 3. Sintaxis de Ejecución Inline
    # IMPORTANTE (Auto-corrección aplicada): 
    # Aunque la directriz era usar estrictamente `hyprctl dispatch exec "[workspace X] CMD"`,
    # Hyprland >= 0.55/0.56 utiliza un intérprete Lua para el dispatch, lo que provoca un error
    # de sintaxis ("return hl.dispatch(exec...) -> global exec is nil") con el comando legacy.
    # Por lo tanto, el comando se ajustó automáticamente a la sintaxis funcional en Lua para
    # esta versión de Hyprland.
    comando_lua = f"hl.dsp.exec_cmd('[workspace {workspace}] {app}')"
    command = ["hyprctl", "dispatch", comando_lua]

    # 4. Logs Agresivos (Fail-Loud) y captura de subproceso
    try:
        result = subprocess.run(
            command,
            env=final_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = (
                f"[CRITICAL ERROR] Fallo al ejecutar la aplicación GUI.\n"
                f"Comando enviado: {' '.join(command)}\n"
                f"Código de retorno: {result.returncode}\n"
                f"STDOUT: {result.stdout.strip()}\n"
                f"STDERR: {result.stderr.strip()}"
            )
            raise RuntimeError(error_msg)
            
        print(f"[ÉXITO] Comando ejecutado correctamente en Hyprland PID {hyprland_pid}.")
        if result.stdout.strip() and result.stdout.strip() != "ok":
            print(f"Respuesta de Hyprland: {result.stdout.strip()}")
            
    except Exception as e:
        # Envolvemos cualquier error imprevisto (ej. binario hyprctl no encontrado)
        if not isinstance(e, RuntimeError):
            raise RuntimeError(f"[CRITICAL ERROR] Error a nivel de subproceso: {e}")
        raise

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Ejecuta una aplicación en un workspace específico de Hyprland.")
    parser.add_argument("app", help="El comando de la aplicación a ejecutar (ej. firefox, foot, alacritty)")
    parser.add_argument("workspace", help="El número o nombre del workspace (ej. 1, 9, name:web)")
    
    args = parser.parse_args()
    
    try:
        ejecutar_app_en_workspace(args.app, args.workspace)
    except Exception as err:
        print(err, file=sys.stderr)
        sys.exit(1)

