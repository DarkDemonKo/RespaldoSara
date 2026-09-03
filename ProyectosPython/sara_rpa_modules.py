import subprocess
import cv2
import os
import time

def open_app_in_workspace(app_command, workspace_num):
    """
    Módulo 1: Gestor de Workspaces.
    Lanza una aplicación en un workspace específico sin robar el foco.
    Aísla estrictamente la inyección del entorno Wayland/Hyprland dinámico para evitar afectar a otros módulos.
    """
    # 1. Recuperar e inyectar el entorno gráfico dinámicamente, exclusivamente para esta función
    target_vars = ['WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR', 'HYPRLAND_INSTANCE_SIGNATURE']
    extracted_env = {}
    
    try:
        uid = os.getuid()
        pids = subprocess.check_output(['pgrep', '-u', str(uid)]).decode().strip().split('\n')
        
        for pid in pids:
            if not pid: continue
            try:
                with open(f'/proc/{pid}/environ', 'rb') as f:
                    environ_data = f.read().split(b'\0')
                    
                temp_env = {}
                for item in environ_data:
                    if b'=' in item:
                        k, v = item.split(b'=', 1)
                        k = k.decode('utf-8', errors='ignore')
                        v = v.decode('utf-8', errors='ignore')
                        if k in target_vars:
                            temp_env[k] = v
                
                if 'HYPRLAND_INSTANCE_SIGNATURE' in temp_env:
                    extracted_env.update(temp_env)
                    if all(var in extracted_env for var in target_vars):
                        break
            except Exception:
                pass
    except Exception as e:
        print(f"Error escaneando procesos para extraer el entorno: {e}")
        
    env = os.environ.copy()
    env.update(extracted_env)
    
    # 2. Construir la orden silent de Hyprland
    hyprctl_cmd = f"[workspace {workspace_num} silent] {app_command}"
    
    try:
        # 3. Lanzar subprocess con el entorno modificado y captura de error estándar
        result = subprocess.run(
            ['hyprctl', 'dispatch', 'exec', hyprctl_cmd],
            env=env,
            capture_output=True,
            text=True
        )
        
        # 4. Loggear explícitamente cualquier falla para depuración en el demonio
        if result.returncode != 0:
            print(f"Error (Wayland/Hyprland) al despachar comando: {result.stderr.strip()}")
        else:
            print(f"Ejecutando '{app_command}' silenciosamente en el workspace {workspace_num}")
            
    except Exception as e:
        print(f"Excepción fatal al invocar subprocess.run: {e}")

def click_on_template(template_path, screenshot_path="/tmp/sara_vision.png", threshold=0.8):
    """
    Módulo 2: Interacción Visual con OpenCV.
    Toma una captura con grim, busca la plantilla usando cv2.matchTemplate 
    y hace clic en el centro exacto utilizando ydotool.
    
    El LLM / Planificador debe estructurar su salida JSON así cuando deba usar "sus ojos":
    {
      "intent": "visual_rpa",
      "action": "click_element",
      "parameters": {
        "template": "/ruta/a/imagenes_rpa/boton_like.png"
      }
    }
    """
    try:
        # 1. Captura de pantalla global usando grim (Específico para Wayland)
        subprocess.run(['grim', screenshot_path], check=True)
        
        # 2. Cargar la captura y la plantilla de referencia
        img_rgb = cv2.imread(screenshot_path)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        
        if template is None:
            print("Error: No se pudo cargar la imagen de referencia.")
            return False
            
        w, h = template.shape[::-1]
        
        # 3. Ejecutar pattern matching
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= threshold:
            # 4. Calcular el centro exacto del objeto encontrado
            center_x = int(max_loc[0] + w / 2)
            center_y = int(max_loc[1] + h / 2)
            
            print(f"Objeto encontrado en la posición ({center_x}, {center_y}) con fiabilidad {max_val:.2f}")
            
            # 5. Mover el cursor y emitir clic izquierdo usando ydotool
            # Nota: ydotoold debe estar corriendo como servicio de root en segundo plano.
            # Movimiento absoluto (-a)
            subprocess.run(['ydotool', 'mousemove', '-a', str(center_x), str(center_y)], check=True)
            time.sleep(0.1) # Breve pausa para asegurar el render del evento 'hover' si existe
            
            # 0xC0 es el código usual para el clic izquierdo en algunas versiones de ydotool
            # En versiones más modernas, `ydotool click 1` es suficiente.
            subprocess.run(['ydotool', 'click', '0xC0'], check=True) 
            
            return True
        else:
            print("No se encontró el patrón en la pantalla.")
            return False
            
    except Exception as e:
        print(f"Error en la interacción visual: {e}")
        return False
